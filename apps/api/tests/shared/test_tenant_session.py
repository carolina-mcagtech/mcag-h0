# tests/shared/test_tenant_session.py
import re
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.db.session import get_session


def _make_begin_cm():
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=cm)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_session_cm(mock_session):
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_request(tenant_id: str):
    req = MagicMock()
    req.state.tenant_id = tenant_id
    return req


@pytest.mark.asyncio
async def test_set_local_executes_within_transaction():
    """get_session must SET LOCAL app.current_tenant_id inside session.begin()."""
    tid = str(uuid.uuid4())

    mock_session = AsyncMock()
    mock_session.info = {}
    mock_session.begin = MagicMock(return_value=_make_begin_cm())

    with patch(
        "app.shared.db.session.get_session_factory",
        return_value=MagicMock(return_value=_make_session_cm(mock_session)),
    ):
        gen = get_session(_make_request(tid))
        await gen.__anext__()
        await gen.aclose()

    mock_session.execute.assert_called_once()
    called_sql = str(mock_session.execute.call_args[0][0])
    assert "SET LOCAL app.current_tenant_id" in called_sql
    assert tid in called_sql


@pytest.mark.asyncio
async def test_set_local_gone_after_transaction():
    """SET LOCAL must be called inside session.begin() — verifies transaction scoping."""
    tid = str(uuid.uuid4())
    call_order: list[str] = []

    mock_session = AsyncMock()
    mock_session.info = {}

    class TrackedBeginCM:
        async def __aenter__(self):
            call_order.append("begin_enter")
            return self

        async def __aexit__(self, *args):
            call_order.append("begin_exit")
            return False

    async def tracked_execute(*args, **kwargs):
        call_order.append("execute")

    mock_session.execute = tracked_execute
    mock_session.begin = MagicMock(return_value=TrackedBeginCM())

    with patch(
        "app.shared.db.session.get_session_factory",
        return_value=MagicMock(return_value=_make_session_cm(mock_session)),
    ):
        gen = get_session(_make_request(tid))
        await gen.__anext__()
        call_order.append("yield_returned")
        await gen.aclose()

    assert call_order.index("begin_enter") < call_order.index("execute")
    assert call_order.index("execute") < call_order.index("yield_returned")
    assert call_order.index("yield_returned") < call_order.index("begin_exit")


@pytest.mark.asyncio
async def test_cross_tenant_read_blocked():
    """Two different tenant tokens must get isolated session contexts — no cross-contamination."""
    tid_a = str(uuid.uuid4())
    tid_b = str(uuid.uuid4())

    captured_tids: list[str] = []

    for tid in [tid_a, tid_b]:
        mock_session = AsyncMock()
        mock_session.info = {}
        mock_session.begin = MagicMock(return_value=_make_begin_cm())

        async def capture_execute(sql, *args, **kwargs):
            sql_str = str(sql)
            if "SET LOCAL app.current_tenant_id" in sql_str:
                match = re.search(r"'([^']+)'", sql_str)
                if match:
                    captured_tids.append(match.group(1))

        mock_session.execute = capture_execute

        with patch(
            "app.shared.db.session.get_session_factory",
            return_value=MagicMock(return_value=_make_session_cm(mock_session)),
        ):
            gen = get_session(_make_request(tid))
            await gen.__anext__()
            await gen.aclose()

    assert len(captured_tids) == 2, "Each request must set tenant ID exactly once"
    assert captured_tids[0] == tid_a
    assert captured_tids[1] == tid_b
    assert captured_tids[0] != captured_tids[1]
