# tests/shared/test_admin_session.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.db.session import get_admin_session


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


@pytest.mark.asyncio
async def test_admin_session_opens_transaction():
    """get_admin_session must open session.begin() — owns transaction lifecycle (ADR-023)."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=_make_begin_cm())

    with patch(
        "app.shared.db.session.get_admin_session_factory",
        return_value=MagicMock(return_value=_make_session_cm(mock_session)),
    ):
        gen = get_admin_session()
        await gen.__anext__()
        await gen.aclose()

    mock_session.begin.assert_called_once()


@pytest.mark.asyncio
async def test_admin_session_no_set_local():
    """get_admin_session must NOT execute SET LOCAL — BYPASSRLS is on the DB user (ADR-010)."""
    mock_session = AsyncMock()
    mock_session.begin = MagicMock(return_value=_make_begin_cm())

    with patch(
        "app.shared.db.session.get_admin_session_factory",
        return_value=MagicMock(return_value=_make_session_cm(mock_session)),
    ):
        gen = get_admin_session()
        await gen.__anext__()
        await gen.aclose()

    mock_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_admin_session_rolls_back_on_error():
    """get_admin_session must propagate exceptions so session.begin() rolls back (ADR-023)."""
    mock_session = AsyncMock()

    rollback_called = False

    class TrackingBeginCM:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            nonlocal rollback_called
            if exc_type is not None:
                rollback_called = True
            return False

    mock_session.begin = MagicMock(return_value=TrackingBeginCM())

    with patch(
        "app.shared.db.session.get_admin_session_factory",
        return_value=MagicMock(return_value=_make_session_cm(mock_session)),
    ):
        gen = get_admin_session()
        await gen.__anext__()
        with pytest.raises(RuntimeError):
            await gen.athrow(RuntimeError("boom"))

    assert rollback_called, "session.begin().__aexit__ must receive the exception for rollback"
