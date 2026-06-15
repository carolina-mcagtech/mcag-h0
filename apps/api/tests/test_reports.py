# tests/test_reports.py
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.config import settings
from app.main import app
from app.shared.db.session import get_session, get_session_factory

_INTERNAL_TOKEN = settings.internal_api_token


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
async def http_client(db_engine):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def full_inspection(db_engine):
    """Tenant + inspector + FULL_INSPECTION-only inspection."""
    tid, insp_id, iid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Rpt Co', 'rptco')"),
            {"id": tid},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:insp_id, :tid, :sub, 'Rpt Inspector', 'inspector@rptco.com', 'HI00010', '2028-01-01')
            """),
            {"insp_id": insp_id, "tid": tid, "sub": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee)
                VALUES (:iid, :tid, :insp_id, '2026-09-01T09:00:00Z', '1 Report Rd, Orlando, FL 32801',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 300.00)
            """),
            {"iid": iid, "tid": tid, "insp_id": insp_id},
        )
    yield tid, iid
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tid})


@pytest_asyncio.fixture
async def wind_mit_inspection(db_engine):
    """Tenant + inspector + inspection with WIND_MITIGATION (INSURANCE-eligible)."""
    tid, insp_id, iid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Wind Co', 'windco')"),
            {"id": tid},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:insp_id, :tid, :sub, 'Wind Inspector', 'inspector@windco.com', 'HI00011', '2028-01-01')
            """),
            {"insp_id": insp_id, "tid": tid, "sub": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee)
                VALUES (:iid, :tid, :insp_id, '2026-09-02T09:00:00Z', '2 Wind Ave, Tampa, FL 33601',
                        ARRAY['WIND_MITIGATION']::inspection_type_enum[], 200.00)
            """),
            {"iid": iid, "tid": tid, "insp_id": insp_id},
        )
    yield tid, iid
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tid})


@pytest_asyncio.fixture
async def two_full_inspections(db_engine):
    """Two independent tenant/inspector/inspection chains for RLS testing."""
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    insp1, insp2 = uuid.uuid4(), uuid.uuid4()
    i1, i2 = uuid.uuid4(), uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain) VALUES
                    (:t1, 'Rpt Alpha', 'rptalpha'),
                    (:t2, 'Rpt Beta',  'rptbeta')
            """),
            {"t1": t1, "t2": t2},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date) VALUES
                    (:insp1, :t1, :sub1, 'Alpha Inspector', 'inspector@rptalpha.com', 'HI00012', '2028-01-01'),
                    (:insp2, :t2, :sub2, 'Beta Inspector',  'inspector@rptbeta.com',  'HI00013', '2028-01-01')
            """),
            {"insp1": insp1, "t1": t1, "sub1": uuid.uuid4(), "insp2": insp2, "t2": t2, "sub2": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee) VALUES
                    (:i1, :t1, :insp1, '2026-09-10T09:00:00Z', '10 Alpha St, Miami, FL 33101',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 250.00),
                    (:i2, :t2, :insp2, '2026-09-11T09:00:00Z', '20 Beta Blvd, Naples, FL 34101',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 275.00)
            """),
            {"i1": i1, "t1": t1, "insp1": insp1, "i2": i2, "t2": t2, "insp2": insp2},
        )
    yield (t1, i1), (t2, i2)
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1, t2]},
        )


# ── Test 1: create FULL report job for any inspection ────────────────────────


async def test_create_full_report_job(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        resp = await http_client.post(
            f"/inspections/{iid}/reports",
            json={"template": "FULL"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["template"] == "FULL"
        assert body["status"] == "PENDING"
        assert body["template_version"] == "v1.0"
        assert body["inspection_id"] == str(iid)
        assert body["tenant_id"] == str(tid)
        assert body["s3_url"] is None
        assert body["generated_at"] is None
        assert body["error_message"] is None
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 2: create INSURANCE job for inspection with WIND_MITIGATION ─────────


async def test_create_insurance_report_job_wind_mitigation(http_client, wind_mit_inspection):
    tid, iid = wind_mit_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        resp = await http_client.post(
            f"/inspections/{iid}/reports",
            json={"template": "INSURANCE"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["template"] == "INSURANCE"
        assert body["status"] == "PENDING"
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 3: reject INSURANCE job for FULL_INSPECTION-only inspection ─────────


async def test_reject_insurance_job_for_full_inspection_only(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        resp = await http_client.post(
            f"/inspections/{iid}/reports",
            json={"template": "INSURANCE"},
        )
        assert resp.status_code == 422
        assert "INSURANCE template" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 4: reject duplicate job (same inspection + template) ─────────────────


async def test_reject_duplicate_report_job(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        payload = {"template": "FULL"}

        first = await http_client.post(f"/inspections/{iid}/reports", json=payload)
        assert first.status_code == 201

        second = await http_client.post(f"/inspections/{iid}/reports", json=payload)
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 5: list report jobs for an inspection ────────────────────────────────


async def test_list_report_jobs(http_client, wind_mit_inspection):
    tid, iid = wind_mit_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        for template in ("FULL", "INSURANCE"):
            resp = await http_client.post(
                f"/inspections/{iid}/reports", json={"template": template}
            )
            assert resp.status_code == 201

        list_resp = await http_client.get(f"/inspections/{iid}/reports")
        assert list_resp.status_code == 200
        jobs = list_resp.json()
        assert len(jobs) == 2
        for job in jobs:
            assert job["inspection_id"] == str(iid)
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 6: get a single report job ─────────────────────────────────────────────


async def test_get_report_job(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        create_resp = await http_client.post(
            f"/inspections/{iid}/reports", json={"template": "FULL"}
        )
        job_id = create_resp.json()["id"]

        get_resp = await http_client.get(f"/inspections/{iid}/reports/{job_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == job_id
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_get_report_job_not_found(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        resp = await http_client.get(f"/inspections/{iid}/reports/{uuid.uuid4()}")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 7: update job status to COMPLETE with s3_url ────────────────────────


async def test_update_job_status_complete(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        create_resp = await http_client.post(
            f"/inspections/{iid}/reports", json={"template": "FULL"}
        )
        assert create_resp.status_code == 201
        job_id = create_resp.json()["id"]

        expected_s3 = f"{tid}/full/{iid}/{job_id}.pdf"
        update_resp = await http_client.post(
            f"/inspections/{iid}/reports/{job_id}/status",
            json={"status": "COMPLETE", "s3_url": expected_s3},
            headers={"X-Internal-Token": _INTERNAL_TOKEN},
        )
        assert update_resp.status_code == 200
        body = update_resp.json()
        assert body["status"] == "COMPLETE"
        assert body["s3_url"] == expected_s3
        assert body["generated_at"] is not None
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 7b: internal callback blocked without valid token ────────────────────


async def test_status_callback_requires_internal_token(http_client, full_inspection):
    tid, iid = full_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        create_resp = await http_client.post(
            f"/inspections/{iid}/reports", json={"template": "FULL"}
        )
        job_id = create_resp.json()["id"]

        resp = await http_client.post(
            f"/inspections/{iid}/reports/{job_id}/status",
            json={"status": "COMPLETE"},
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 8: 404 for an inspection that belongs to another tenant ─────────────


async def test_reports_inspection_not_in_tenant(http_client, two_full_inspections):
    (t1, i1), (t2, i2) = two_full_inspections
    app.dependency_overrides[get_session] = _session_override(t1)
    try:
        resp = await http_client.post(
            f"/inspections/{i2}/reports", json={"template": "FULL"}
        )
        assert resp.status_code == 404

        resp = await http_client.get(f"/inspections/{i2}/reports")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 9: RLS — cannot access other tenant's report jobs ────────────────────


async def test_rls_report_job_isolation(db_engine, two_full_inspections):
    (t1, i1), (t2, i2) = two_full_inspections
    jid = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO report_jobs (id, tenant_id, inspection_id, template)
                VALUES (:jid, :tid, :iid, 'FULL')
            """),
            {"jid": jid, "tid": t1, "iid": i1},
        )

    # Tenant 2 must not see tenant 1's job
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (await conn.execute(text("SELECT id FROM report_jobs"))).fetchall()
    assert len(rows) == 0

    # Tenant 1 sees its own job
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1}'"))
        rows = (await conn.execute(text("SELECT id FROM report_jobs"))).fetchall()
    assert len(rows) == 1
    assert rows[0].id == jid
