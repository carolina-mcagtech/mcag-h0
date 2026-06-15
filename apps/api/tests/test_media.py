# tests/test_media.py
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.shared.db.session import get_session, get_session_factory


def _session_override(tenant_id: uuid.UUID):
    async def _override():
        async with get_session_factory()() as session:
            async with session.begin():
                # db_engine connects as superuser, which bypasses RLS entirely.
                # Switch to app_role so RLS policies are actually enforced.
                await session.execute(text("SET LOCAL ROLE app_role"))
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")
                )
                session.info["tenant_id"] = tenant_id
                yield session
    return _override


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def seeded_inspection(db_engine):
    """Seed tenant → inspector → inspection; yield (tenant_id, inspection_id)."""
    tid = uuid.uuid4()
    insp_id = uuid.uuid4()
    iid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Media Co', 'mediaco')"),
            {"id": tid},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:insp_id, :tid, :sub, 'Media Inspector', 'inspector@mediaco.com', 'HI00007', '2028-01-01')
            """),
            {"insp_id": insp_id, "tid": tid, "sub": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee)
                VALUES (:iid, :tid, :insp_id, '2026-08-01T09:00:00Z', '10 Media Ln, Orlando, FL 32801',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 300.00)
            """),
            {"iid": iid, "tid": tid, "insp_id": insp_id},
        )
    yield tid, iid
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tid})


@pytest_asyncio.fixture
async def two_seeded_inspections(db_engine):
    """Two independent tenant/inspector/inspection chains; yield ((t1,i1), (t2,i2))."""
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    insp1, insp2 = uuid.uuid4(), uuid.uuid4()
    i1, i2 = uuid.uuid4(), uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain) VALUES
                    (:t1, 'Media Alpha', 'mediaalpha'),
                    (:t2, 'Media Beta',  'mediabeta')
            """),
            {"t1": t1, "t2": t2},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date) VALUES
                    (:insp1, :t1, :sub1, 'Alpha Inspector', 'inspector@mediaalpha.com', 'HI00008', '2028-01-01'),
                    (:insp2, :t2, :sub2, 'Beta Inspector',  'inspector@mediabeta.com',  'HI00009', '2028-01-01')
            """),
            {"insp1": insp1, "t1": t1, "sub1": uuid.uuid4(), "insp2": insp2, "t2": t2, "sub2": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee) VALUES
                    (:i1, :t1, :insp1, '2026-09-01T09:00:00Z', '1 Alpha Way, Miami, FL 33101',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 200.00),
                    (:i2, :t2, :insp2, '2026-09-02T09:00:00Z', '2 Beta Way, Tampa, FL 33601',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 200.00)
            """),
            {"i1": i1, "t1": t1, "insp1": insp1, "i2": i2, "t2": t2, "insp2": insp2},
        )
    yield (t1, i1), (t2, i2)
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1, t2]},
        )


@pytest_asyncio.fixture
async def http_client(db_engine, seeded_inspection):
    tid, _ = seeded_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


def _media_payload(**kwargs) -> dict:
    return {
        "filename": "photo.jpg",
        "content_type": "image/jpeg",
        "s3_key": f"uploads/{uuid.uuid4()}.jpg",
        "s3_bucket": "mcag-media-dev",
        **kwargs,
    }


# ── Test 1: create media asset ────────────────────────────────────────────────


async def test_create_media(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    payload = _media_payload()
    resp = await http_client.post(f"/inspections/{iid}/media", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["inspection_id"] == str(iid)
    assert body["tenant_id"] == str(tid)
    assert body["filename"] == payload["filename"]
    assert body["content_type"] == payload["content_type"]
    assert body["s3_key"] == payload["s3_key"]
    assert body["s3_bucket"] == payload["s3_bucket"]


# ── Test 2: list media assets by inspection ─────────────────────────────────────


async def test_list_media(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    for name in ("photo1.jpg", "photo2.jpg", "photo3.png"):
        resp = await http_client.post(
            f"/inspections/{iid}/media", json=_media_payload(filename=name)
        )
        assert resp.status_code == 201

    list_resp = await http_client.get(f"/inspections/{iid}/media")
    assert list_resp.status_code == 200
    assets = list_resp.json()
    assert len(assets) == 3
    for a in assets:
        assert a["inspection_id"] == str(iid)


# ── Test 3: get a single media asset ────────────────────────────────────────────


async def test_get_media(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    create_resp = await http_client.post(
        f"/inspections/{iid}/media", json=_media_payload()
    )
    media_id = create_resp.json()["id"]

    get_resp = await http_client.get(f"/inspections/{iid}/media/{media_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == media_id


async def test_get_media_not_found(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.get(f"/inspections/{iid}/media/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Test 4: delete media asset ──────────────────────────────────────────────────


async def test_delete_media(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    create_resp = await http_client.post(
        f"/inspections/{iid}/media", json=_media_payload()
    )
    media_id = create_resp.json()["id"]

    delete_resp = await http_client.delete(f"/inspections/{iid}/media/{media_id}")
    assert delete_resp.status_code == 204

    list_resp = await http_client.get(f"/inspections/{iid}/media")
    assert list_resp.status_code == 200
    assert list_resp.json() == []


async def test_delete_media_not_found(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.delete(f"/inspections/{iid}/media/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Test 5: 404 for an inspection that belongs to another tenant ────────────────


async def test_media_inspection_not_in_tenant(http_client, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections

    resp = await http_client.post(f"/inspections/{i2}/media", json=_media_payload())
    assert resp.status_code == 404

    resp = await http_client.get(f"/inspections/{i2}/media")
    assert resp.status_code == 404


# ── Test 6: RLS — cannot access another tenant's media assets ───────────────────


async def test_rls_media_asset_isolation(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections
    asset_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO media_assets
                    (id, tenant_id, inspection_id, filename, content_type, s3_key, s3_bucket)
                VALUES
                    (:aid, :tid, :iid, 'photo.jpg', 'image/jpeg', :s3key, 'mcag-media-dev')
            """),
            {"aid": asset_id, "tid": t1, "iid": i1, "s3key": f"uploads/{asset_id}.jpg"},
        )

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (await conn.execute(text("SELECT id FROM media_assets"))).fetchall()
    assert len(rows) == 0

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1}'"))
        rows = (await conn.execute(text("SELECT id FROM media_assets"))).fetchall()
    assert len(rows) == 1
    assert rows[0].id == asset_id
