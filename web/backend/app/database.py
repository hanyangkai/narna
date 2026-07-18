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

    if "organizations" in tables:
        cols = {c["name"] for c in insp.get_columns("organizations")}
        alterations = []
        if "gu_in_period" not in cols:
            alterations.append("ADD COLUMN gu_in_period INTEGER DEFAULT 0")
        if "telemetry_opt_in" not in cols:
            alterations.append("ADD COLUMN telemetry_opt_in INTEGER DEFAULT 0")
        if "train_opt_in" not in cols:
            alterations.append("ADD COLUMN train_opt_in INTEGER DEFAULT 0")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE organizations {clause}"))

    if "runs" in tables:
        cols = {c["name"] for c in insp.get_columns("runs")}
        alterations: list[str] = []
        if "session_id" not in cols:
            alterations.append("ADD COLUMN session_id VARCHAR(80)")
        if "total_gu" not in cols:
            alterations.append("ADD COLUMN total_gu INTEGER DEFAULT 0")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE runs {clause}"))

    if "registry_agents" in tables:
        cols = {c["name"] for c in insp.get_columns("registry_agents")}
        alterations = []
        if "certification_json" not in cols:
            alterations.append("ADD COLUMN certification_json TEXT")
        if "verified" not in cols:
            alterations.append("ADD COLUMN verified INTEGER DEFAULT 0")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE registry_agents {clause}"))

    if "registry_governance_packages" in tables:
        cols = {c["name"] for c in insp.get_columns("registry_governance_packages")}
        alterations = []
        for name, decl in (
            ("price_usd", "INTEGER DEFAULT 0"),
            ("take_rate_bps", "INTEGER DEFAULT 2000"),
            ("author_revenue_usd", "INTEGER DEFAULT 0"),
            ("platform_revenue_usd", "INTEGER DEFAULT 0"),
        ):
            if name not in cols:
                alterations.append(f"ADD COLUMN {name} {decl}")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE registry_governance_packages {clause}"))

    if "marketplace_purchases" in tables:
        cols = {c["name"] for c in insp.get_columns("marketplace_purchases")}
        alterations = []
        if "status" not in cols:
            alterations.append("ADD COLUMN status VARCHAR(32) DEFAULT 'paid'")
        if "stripe_session_id" not in cols:
            alterations.append("ADD COLUMN stripe_session_id VARCHAR(255)")
        if alterations:
            with engine.begin() as conn:
                for clause in alterations:
                    conn.execute(text(f"ALTER TABLE marketplace_purchases {clause}"))


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_schema()
