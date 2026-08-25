"""Tests for Capability Governor (NGS-0015)."""

from __future__ import annotations

import unittest
from pathlib import Path

from uap.capability_gov import CapabilityGovernor

DEFAULT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "uap"
    / "_packages"
    / "capability-passport-default.yaml"
)


class CapabilityGovernorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gov = CapabilityGovernor()

    def test_create_agent_restricted(self) -> None:
        out = self.gov.evaluate(capability="create.agent", path=DEFAULT)
        self.assertEqual(out["decision"], "restricted")
        self.assertTrue(out["requiredApprovals"])

    def test_wallet_deny(self) -> None:
        out = self.gov.evaluate(capability="wallet", path=DEFAULT)
        self.assertEqual(out["decision"], "deny")

    def test_search_allow(self) -> None:
        out = self.gov.evaluate(capability="search", path=DEFAULT)
        self.assertEqual(out["decision"], "allow")

    def test_whitelist_miss_denies(self) -> None:
        out = self.gov.evaluate(
            capability="mcp",
            path=DEFAULT,
            target="mcp://evil.example",
        )
        self.assertEqual(out["decision"], "deny")

    def test_default_guardian_profile(self) -> None:
        out = self.gov.evaluate(capability="create.agent", profile="guardian")
        self.assertIn(out["decision"], {"restricted", "deny"})


if __name__ == "__main__":
    unittest.main()
