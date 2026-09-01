from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.request
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .billing import add_plan_period, normalize_plan, now_utc
from .crypto_chains import TRANSFER_TOPIC, get_rpc_url, get_token
from .database import SessionLocal
from .invoice_utils import expire_pending_invoices
from .models import Organization, PaymentInvoice

logger = logging.getLogger("uap-crypto-bot")


def _rpc_call(rpc_url: str, method: str, params: list) -> dict:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode("utf-8")
    req = urllib.request.Request(
        rpc_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "narna-crypto-bot/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _topic_address(addr: str) -> str:
    a = addr.lower().replace("0x", "")
    return "0x" + ("0" * 24) + a


def _to_raw_amount(amount_str: str, decimals: int) -> int:
    v = float(amount_str)
    return int(round(v * (10**decimals)))


def _mark_invoice_paid(
    db: Session, inv: PaymentInvoice, tx_hash: str, block_number: int
) -> None:
    # One on-chain tx can only fulfill one invoice
    clash = (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.tx_hash == tx_hash,
            PaymentInvoice.status == "paid",
            PaymentInvoice.id != inv.id,
        )
        .first()
    )
    if clash is not None:
        logger.warning(
            "tx already used",
            extra={"tx_hash": tx_hash, "invoice_id": inv.invoice_id},
        )
        return

    inv.status = "paid"
    inv.tx_hash = tx_hash
    inv.block_number = block_number
    inv.paid_at = datetime.now(timezone.utc)

    org = db.query(Organization).filter(Organization.id == inv.org_id).first()
    if org is not None:
        org.plan = normalize_plan(inv.plan)
        now = now_utc()
        org.period_start_at = now
        org.plan_expires_at = add_plan_period(now)
        org.events_in_period = 0
        org.gu_in_period = 0
        if hasattr(org, "adqa_checks_in_period"):
            org.adqa_checks_in_period = 0
        seats = int(getattr(inv, "seat_count", 0) or 0)
        if seats > 0:
            org.seat_count = seats
        elif org.plan == "team" and int(getattr(org, "seat_count", 1) or 1) < 3:
            org.seat_count = 3
        if getattr(org, "email", None):
            try:
                from .mail import send_payment_confirmed_email

                send_payment_confirmed_email(
                    to=str(org.email),
                    plan=normalize_plan(inv.plan),
                    amount=str(inv.expected_amount),
                    asset=str(inv.asset or "usdc"),
                    network=str(inv.network or "base"),
                    expires_at=(
                        org.plan_expires_at.isoformat() if org.plan_expires_at else None
                    ),
                )
            except Exception:
                logger.exception("payment email failed")


def _scan_invoice(
    *,
    inv: PaymentInvoice,
    rpc_url: str,
    from_block: int,
    latest_block: int,
    min_confirmations: int,
) -> tuple[str, int] | None:
    network = (inv.network or "ethereum").lower()
    asset = (inv.asset or "usdc").lower()
    token = get_token(network, asset)
    if token is None:
        return None

    expected_raw = _to_raw_amount(inv.expected_amount, token.decimals)
    topics = [TRANSFER_TOPIC, None, _topic_address(inv.recipient_wallet)]
    logs_resp = _rpc_call(
        rpc_url,
        "eth_getLogs",
        [
            {
                "fromBlock": hex(from_block),
                "toBlock": hex(latest_block),
                "address": token.address,
                "topics": topics,
            }
        ],
    )
    logs = logs_resp.get("result", [])
    for lg in logs:
        amount_raw = int(lg.get("data", "0x0"), 16)
        # Exact amount match (unique cents per pending invoice)
        if amount_raw != expected_raw:
            continue
        tx_hash = lg.get("transactionHash", "")
        block_number = int(lg.get("blockNumber", "0x0"), 16)
        if latest_block - block_number + 1 < min_confirmations:
            continue
        return tx_hash, block_number
    return None


def run_once() -> None:
    db = SessionLocal()
    try:
        expired = expire_pending_invoices(db)
        if expired:
            logger.info("expired invoices", extra={"count": expired})
            db.commit()

        mode = os.environ.get("UAP_CRYPTO_MODE", "mock").lower()
        if mode != "live":
            return

        pending = (
            db.query(PaymentInvoice)
            .filter(PaymentInvoice.status == "pending", PaymentInvoice.kind == "crypto")
            .limit(100)
            .all()
        )
        if not pending:
            return

        scan_blocks = int(os.environ.get("UAP_CRYPTO_SCAN_BLOCKS", "6000"))
        min_confirmations = int(os.environ.get("UAP_CRYPTO_MIN_CONFIRMATIONS", "3"))

        # Group by network to avoid duplicate RPC calls.
        by_network: dict[str, list[PaymentInvoice]] = {}
        for inv in pending:
            by_network.setdefault((inv.network or "ethereum").lower(), []).append(inv)

        for network, invoices in by_network.items():
            rpc_url = get_rpc_url(network)
            if not rpc_url:
                continue

            latest_resp = _rpc_call(rpc_url, "eth_blockNumber", [])
            latest_hex = latest_resp.get("result", "0x0")
            latest_block = int(latest_hex, 16)
            from_block = max(0, latest_block - scan_blocks)

            for inv in invoices:
                match = _scan_invoice(
                    inv=inv,
                    rpc_url=rpc_url,
                    from_block=from_block,
                    latest_block=latest_block,
                    min_confirmations=min_confirmations,
                )
                if match is None:
                    continue
                tx_hash, block_number = match
                _mark_invoice_paid(db, inv, tx_hash, block_number)
                logger.info(
                    "invoice paid",
                    extra={
                        "invoice_id": inv.invoice_id,
                        "network": network,
                        "tx_hash": tx_hash,
                    },
                )

        db.commit()
    finally:
        db.close()


def start_background_bot() -> None:
    enabled = os.environ.get("UAP_CRYPTO_BOT_ENABLED", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    if not enabled:
        return

    interval = int(os.environ.get("UAP_CRYPTO_BOT_INTERVAL_SEC", "20"))

    def _loop() -> None:
        while True:
            try:
                run_once()
            except Exception:
                logger.exception("crypto bot scan failed")
            time.sleep(max(5, interval))

    th = threading.Thread(target=_loop, daemon=True, name="uap-crypto-bot")
    th.start()
