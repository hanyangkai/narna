from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("UAP_DATABASE_URL", "sqlite:///./uap_cloud.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_schema() -> None:
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    tables = insp.get_table_names()

    if "payment_invoices" in tables:
        cols = {c["name"] for c in insp.get_columns("payment_invoices")}
        if "expires_at" not in cols:
            col_type = "DATETIME" if DATABASE_URL.startswith("sqlite") else "TIMESTAMP WITH TIME ZONE"
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE payment_invoices ADD COLUMN expires_at {col_type}"))

    if "registry_agents" in tables:
        cols = {c["name"] for c in insp.get_columns("registry_agents")}
        alterations: list[str] = []
        if "certification_json" not in cols:
            alterations.append("ADD COLUMN certification_json TEXT")
        if "verified" not in cols:
            alterations.append("ADD COLUMN verified INTEGER DEFAULT 0")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE registry_agents {clause}"))


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_schema()
