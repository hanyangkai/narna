from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMAS = REPO / "specs" / "schemas"
NGS = REPO / "rfcs" / "ngs"


class NgsSeriesTest(unittest.TestCase):
    def test_ngs_files_exist(self) -> None:
        for i in range(1, 14):
            matches = list(NGS.glob(f"NGS-{i:04d}-*.md"))
            self.assertEqual(len(matches), 1, f"missing NGS-{i:04d}")

    def test_core_schemas_exist(self) -> None:
        for name in (
            "capability.schema.json",
            "policy-pack.schema.json",
            "audit.schema.json",
            "certification.schema.json",
            "trust-score.schema.json",
            "evidence.schema.json",
            "passport.schema.json",
        ):
            self.assertTrue((SCHEMAS / name).exists(), name)

    def test_policy_pack_example_validates(self) -> None:
        try:
            import jsonschema
            import yaml
        except ImportError:
            self.skipTest("jsonschema/yaml not installed")
        schema = json.loads((SCHEMAS / "policy-pack.schema.json").read_text(encoding="utf-8"))
        doc = yaml.safe_load(
            (REPO / "specs" / "examples" / "policy-pack-local-default.yaml").read_text(encoding="utf-8")
        )
        jsonschema.validate(doc, schema)

    def test_openapi_exists(self) -> None:
        path = REPO / "specs" / "governance-api" / "openapi.yaml"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("/v1/passport/{agentId}", text)
        self.assertIn("/v1/policy/evaluate", text)


if __name__ == "__main__":
    unittest.main()
