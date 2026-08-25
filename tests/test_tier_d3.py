"""Tier D slice 3 — partner runtime certification + society CTI demo primitives."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class PartnerCertTest(unittest.TestCase):
    def test_certify_docker_and_k8s(self) -> None:
        from uap.partner_cert import PartnerRuntimeCertifier

        with tempfile.TemporaryDirectory() as td:
            certifier = PartnerRuntimeCertifier(td)
            d = certifier.certify("docker")
            self.assertTrue(d["valid"])
            self.assertIn(d["level"], ("L2", "L3"))
            self.assertEqual(d["passed"], d["total"])
            k = certifier.certify("kubernetes")
            self.assertTrue(k["valid"])
            self.assertEqual(k["level"], "L1")
            l3 = certifier.certify("kubernetes", attested=True)
            self.assertEqual(l3["level"], "L3")
            self.assertEqual(len(certifier.list()), 2)  # docker + kubernetes overwrite same k8s
            v = certifier.verify("docker")
            self.assertTrue(v["ok"])

    def test_export_import_bundle(self) -> None:
        from uap.partner_cert import PartnerRuntimeCertifier

        with tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
            a = PartnerRuntimeCertifier(ta)
            a.certify("docker")
            bundle = a.export_bundle()
            b = PartnerRuntimeCertifier(tb)
            out = b.import_bundle(bundle)
            self.assertEqual(out["imported"], 1)
            self.assertIsNotNone(b.get("docker"))

    def test_isolation_list_includes_cert_level(self) -> None:
        from uap.isolation_partner import IsolationRegistry
        from uap.partner_cert import PartnerRuntimeCertifier

        with tempfile.TemporaryDirectory() as td:
            PartnerRuntimeCertifier(td).certify("docker")
            partners = IsolationRegistry(td).list()
            docker = next(p for p in partners if p["name"] == "docker")
            self.assertNotEqual(docker["certLevel"], "L0")


class SocietyDemoImportTest(unittest.TestCase):
    def test_local_demo_ok(self) -> None:
        # Import demo function without running as script
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "scripts" / "cti_society_demo.py"
        spec = importlib.util.spec_from_file_location("cti_society_demo", path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = mod.demo_local()
        self.assertTrue(out["ok"])
        self.assertEqual(out["orgA"]["dockerCert"], "L2")


if __name__ == "__main__":
    unittest.main()
