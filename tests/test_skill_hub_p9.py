"""P9 Skills Hub network + B6 layout alias tests."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from narna.decision import DecisionTraceStore, replay_trace
from narna.runtime import ModelRouter, NarnaAgent
from uap.skill_hub import SkillHub


class SkillHubNetworkTests(unittest.TestCase):
    def test_zip_roundtrip(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            hub = SkillHub(td)
            hub.publish(name="Review NDA", body="Check liability caps.", tags=["legal"])
            zpath = Path(td) / "out.zip"
            exp = hub.export_zip(zpath)
            self.assertTrue(exp["ok"])
            self.assertGreaterEqual(exp["n"], 1)
            hub2 = SkillHub(Path(td) / "other")
            imp = hub2.import_zip(zpath)
            self.assertTrue(imp["ok"])
            self.assertGreaterEqual(imp["n"], 1)
            names = [s["name"] for s in hub2.list_public()]
            self.assertIn("Review NDA", names)

    def test_sync_from_local_index(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            idx = Path(td) / "index.json"
            idx.write_text(
                json.dumps(
                    {
                        "skills": [
                            {
                                "skillId": "hub_remote_1",
                                "name": "Remote Skill",
                                "body": "Do the thing carefully.",
                                "tags": ["remote"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            hub = SkillHub(Path(td) / "ws")
            out = hub.sync_from_url(str(idx))
            self.assertTrue(out["ok"])
            self.assertEqual(out["added"], 1)
            self.assertTrue(hub.get("hub_remote_1"))

    def test_autopublish_gated(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            hub = SkillHub(td)
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("UAP_SKILL_HUB_AUTOPUBLISH", None)
                self.assertIsNone(
                    hub.maybe_autopublish(name="x", body="y", dqs=90)
                )
            with mock.patch.dict(os.environ, {"UAP_SKILL_HUB_AUTOPUBLISH": "1"}):
                row = hub.maybe_autopublish(name="Good skill", body="Procedure", dqs=85)
                self.assertIsNotNone(row)
                self.assertEqual(row["name"], "Good skill")
                self.assertIsNone(
                    hub.maybe_autopublish(name="Low", body="nope", dqs=70)
                )


class LayoutAliasTests(unittest.TestCase):
    def test_runtime_aliases(self):
        self.assertTrue(callable(NarnaAgent))
        self.assertTrue(callable(ModelRouter))

    def test_decision_aliases(self):
        self.assertTrue(callable(DecisionTraceStore))
        self.assertTrue(callable(replay_trace))


if __name__ == "__main__":
    unittest.main()
