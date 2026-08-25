"""UAP Cloud backend package.

Avoid importing ``main`` at package load — it starts the crypto bot and
rate-limit middleware. Access ``app`` lazily via ``from web.backend.app import app``.
"""

from .database import Base, SessionLocal, engine, get_db, init_db

__all__ = ["app", "Base", "SessionLocal", "engine", "get_db", "init_db"]


def __getattr__(name: str):
    if name == "app":
        from .main import app as _app

        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
