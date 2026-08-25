"""Billing hardening: unique amounts, seats, plan expiry helpers."""
from __future__ import annotations

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from web.backend.app.billing import add_plan_period, checkout_usd_amount, normalize_plan
from web.backend.app.invoice_utils import allocate_unique_amount
from web.backend.app.quota import _downgrade_if_plan_expired


def _mock_plan_allowed_logic() -> bool:
    flag = os.environ.get("UAP_ALLOW_MOCK_PLAN", "").lower()
    if flag in {"1", "true", "yes"}:
        return True
    if flag in {"0", "false", "no"}:
        return False
    return os.environ.get("UAP_CRYPTO_MODE", "mock").lower() != "live"


class BillingCheckoutAmountTests(unittest.TestCase):
    def test_cloud_flat(self):
        usd, seats = checkout_usd_amount("cloud")
        self.assertEqual(usd, 20.0)
        self.assertEqual(seats, 1)

    def test_team_seats(self):
        usd, seats = checkout_usd_amount("team", seats=5)
        self.assertEqual(usd, 495.0)
        self.assertEqual(seats, 5)

    def test_team_clamp(self):
        usd, seats = checkout_usd_amount("team", seats=1)
        self.assertEqual(seats, 3)
        self.assertEqual(usd, 297.0)
        usd2, seats2 = checkout_usd_amount("team", seats=99)
        self.assertEqual(seats2, 50)
        self.assertEqual(usd2, 4950.0)


class UniqueAmountTests(unittest.TestCase):
    def test_allocates_unique_cents(self):
        db = MagicMock()
        inv = MagicMock()
        inv.expected_amount = "20.00"
        db.query.return_value.filter.return_value.all.return_value = [inv]
        amt = allocate_unique_amount(db, network="base", asset="usdc", base_usd=20.0)
        self.assertEqual(amt, "20.01")


class PlanExpiryTests(unittest.TestCase):
    def test_add_period(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = add_plan_period(start)
        self.assertEqual(end, start + timedelta(days=30))

    def test_downgrade_expired(self):
        org = MagicMock()
        org.plan = "cloud"
        org.plan_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        org.seat_count = 1
        _downgrade_if_plan_expired(org)
        self.assertEqual(org.plan, "free")

    def test_mock_gate(self):
        os.environ["UAP_CRYPTO_MODE"] = "live"
        os.environ.pop("UAP_ALLOW_MOCK_PLAN", None)
        self.assertFalse(_mock_plan_allowed_logic())
        os.environ["UAP_ALLOW_MOCK_PLAN"] = "1"
        self.assertTrue(_mock_plan_allowed_logic())
        os.environ["UAP_CRYPTO_MODE"] = "mock"
        os.environ.pop("UAP_ALLOW_MOCK_PLAN", None)
        self.assertTrue(_mock_plan_allowed_logic())
        self.assertEqual(normalize_plan("pro"), "cloud")


if __name__ == "__main__":
    unittest.main()
