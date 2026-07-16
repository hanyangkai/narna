from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    level = os.environ.get("UAP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def init_sentry_if_configured() -> bool:
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore
    except Exception:
        return False

    env = os.environ.get("SENTRY_ENVIRONMENT", "production")
    traces_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        traces_sample_rate=traces_rate,
        integrations=[FastApiIntegration()],
    )
    return True

