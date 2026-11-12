"""Process-level AsyncSqliteSaver for LangGraph pause/resume (HITL)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.config import get_settings

log = logging.getLogger(__name__)

_checkpointer: AsyncSqliteSaver | None = None


def checkpoints_db_path() -> str:
    """Absolute-ish path string for the SQLite checkpoint file."""
    return str(get_settings().data_path / "checkpoints.db")


def get_checkpointer() -> AsyncSqliteSaver:
    """Return the app-scoped async checkpointer (must be opened in lifespan)."""
    if _checkpointer is None:
        raise RuntimeError(
            "AsyncSqliteSaver is not initialized. Open it in the FastAPI lifespan before serving traffic."
        )
    return _checkpointer


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[AsyncSqliteSaver]:
    """Open AsyncSqliteSaver for the process lifetime and tear it down on exit."""
    global _checkpointer
    path = checkpoints_db_path()
    async with AsyncSqliteSaver.from_conn_string(path) as checkpointer:
        await checkpointer.setup()
        _checkpointer = checkpointer
        log.info("LangGraph AsyncSqliteSaver ready at %s", path)
        try:
            yield checkpointer
        finally:
            _checkpointer = None
            log.info("LangGraph AsyncSqliteSaver closed")
