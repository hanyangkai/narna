from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class UniversalIdentityTest(unittest.TestCase):
    def test_issue_tool_and_mcp_identities(self) -> None:
        from narna import ENTITY_KINDS, IdentityStore
        from uap.hashing import sha256_obj

        self.assertIn("Tool", ENTITY_KINDS)
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            store = IdentityStore(ws)
            tool = store.issue_entity(
                kind="Tool",
                entity_id="tool_browser_01",
                owner="did:narna:org:example",
                version="1.0.0",
                content_hash=sha256_obj({"name": "browser"}),
                origin="https://example.com/tools/browser",
                license="MIT",
            )
            self.assertEqual(tool["kind"], "Tool")
            self.assertTrue(tool["identityId"].startswith("idnt_"))
            mcp = store.issue_entity(
                kind="McpServer",
                entity_id="mcp_fs_01",
                owner="did:narna:org:example",
                version="0.2.0",
                content_hash=sha256_obj({"server": "fs"}),
            )
            self.assertEqual(mcp["kind"], "McpServer")
            self.assertEqual(len(store.list_entities()), 2)

    def test_agent_passport_cites_constitution(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("IdAgent", workspace=ws)
            entity = ws / ".uap" / "identity" / "entities" / f"{agent.spec.agent_id}.json"
            self.assertTrue(entity.exists())
            passport = agent.passport(refresh=True)
            self.assertIn("constitution", passport)
            self.assertIn("constitutionId", passport["constitution"])
            self.assertTrue(passport["constitution"]["constitutionHash"].startswith("sha256:"))

    def test_example_universal_identity_schema(self) -> None:
        import json

        from uap.schemas import validator_for

        raw = json.loads(
            (REPO / "specs" / "examples" / "universal-identity.json").read_text(encoding="utf-8")
        )
        validator_for("universal-identity.schema.json").validate(raw)


if __name__ == "__main__":
    unittest.main()
