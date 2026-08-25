"""SaaS drop-in — quotas, tenants, MCP discovery."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class BillingPlansTest(unittest.TestCase):
    def test_cloud_alias_and_caps(self) -> None:
        sys.path.insert(0, str(REPO / "web" / "backend"))
        from app.billing import (
            normalize_plan,
            plan_adqa_hard_cap,
            plan_adqa_soft_cap,
            plan_price_cents,
            plan_usd_price,
        )

        self.assertEqual(normalize_plan("pro"), "cloud")
        self.assertEqual(plan_usd_price("cloud"), 20.0)
        self.assertEqual(plan_price_cents("cloud"), 2000)
        self.assertEqual(plan_adqa_soft_cap("free"), 100)
        self.assertEqual(plan_adqa_hard_cap("free"), 500)
        self.assertIsNone(plan_adqa_hard_cap("cloud"))


class TenantMemoryTest(unittest.TestCase):
    def test_tenant_isolation(self) -> None:
        from uap.decision_memory import DecisionMemory

        with tempfile.TemporaryDirectory() as td:
            a = DecisionMemory(td)
            b = DecisionMemory(td)
            ra = a.record(action="x.a", tenant_id="org_1")
            rb = b.record(action="x.b", tenant_id="org_2")
            qa = a.query(tenant_id="org_1")
            qb = b.query(tenant_id="org_2")
            self.assertEqual(len(qa), 1)
            self.assertEqual(qa[0]["decisionId"], ra["decisionId"])
            self.assertEqual(len(qb), 1)
            self.assertEqual(qb[0]["decisionId"], rb["decisionId"])
            self.assertNotEqual(ra["decisionId"], rb["decisionId"])


class QuotaTest(unittest.TestCase):
    def test_free_hard_cap_402(self) -> None:
        from datetime import datetime, timezone

        from fastapi import HTTPException

        sys.path.insert(0, str(REPO / "web" / "backend"))
        from app.models import Organization
        from app.quota import enforce_plan_limit

        org = Organization(name="t", plan="free")
        org.adqa_checks_in_period = 500
        org.events_in_period = 0
        org.gu_in_period = 0
        org.period_start_at = datetime.now(timezone.utc)
        with self.assertRaises(HTTPException) as ctx:
            enforce_plan_limit(org=org, projected_adqa=1)
        self.assertEqual(ctx.exception.status_code, 402)


if __name__ == "__main__":
    unittest.main()
