from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .models import PaymentInvoice


def invoice_ttl_minutes() -> int:
    return int(os.environ.get("UAP_CRYPTO_INVOICE_TTL_MIN", "60"))


def invoice_expires_at(*, now: datetime | None = None) -> datetime:
    base = now or datetime.now(timezone.utc)
    return base + timedelta(minutes=invoice_ttl_minutes())


def expire_pending_invoices(db: Session, *, now: datetime | None = None) -> int:
    """Mark pending crypto invoices past expires_at as expired."""
    ts = now or datetime.now(timezone.utc)
    pending = (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.status == "pending",
            PaymentInvoice.kind == "crypto",
            PaymentInvoice.expires_at.isnot(None),
            PaymentInvoice.expires_at < ts,
        )
        .all()
    )
    for inv in pending:
        inv.status = "expired"
        inv.note = inv.note or "expired: payment window closed"
    return len(pending)


def build_qr_payload(
    *,
    recipient_wallet: str,
    expected_amount: str,
    asset: str,
    network: str,
    invoice_id: str,
) -> str:
    # Simple wallet QR payload — works with most mobile wallets.
    return (
        f"uap://pay?wallet={recipient_wallet}"
        f"&amount={expected_amount}&asset={asset.upper()}"
        f"&network={network}&invoice={invoice_id}"
    )
