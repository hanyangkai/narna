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


def allocate_unique_amount(
    db: Session,
    *,
    network: str,
    asset: str,
    base_usd: float,
) -> str:
    """Pick base + unique cents (01–99) among pending invoices on same rail.

    Avoids two open invoices sharing the same expected amount so on-chain
    Transfer matching can be exact.
    """
    pending = (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.status == "pending",
            PaymentInvoice.kind == "crypto",
            PaymentInvoice.network == network.lower(),
            PaymentInvoice.asset == asset.lower(),
        )
        .all()
    )
    used = {str(inv.expected_amount) for inv in pending}
    base = round(float(base_usd), 2)
    # Prefer exact base if free, else base + 0.01 … 0.99
    candidates = [f"{base:.2f}"] + [f"{base + i / 100:.2f}" for i in range(1, 100)]
    for amt in candidates:
        if amt not in used:
            return amt
    # Extremely unlikely — fall back to micro-unique via timestamp cents
    stamp = int(datetime.now(timezone.utc).timestamp()) % 100
    return f"{base + stamp / 100:.2f}"
