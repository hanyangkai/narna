#!/usr/bin/env python3
"""Society-scale CTI demo — two local orgs + optional live hub mesh.

Local (no network):
  python scripts/cti_society_demo.py

Live hub (push/pull via api.narna.org or self-host):
  python scripts/cti_society_demo.py --hub https://api.narna.org
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def demo_local() -> dict:
    from uap.collective import CollectiveDefense
    from uap.cti_hub import CTIHub
    from uap.cti_mesh import CTIMesh
    from uap.partner_cert import PartnerRuntimeCertifier

    with tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
        org_a = Path(ta)
        org_b = Path(tb)
        CollectiveDefense(org_a).set_opt_in(True)
        CollectiveDefense(org_b).set_opt_in(True)

        sig = CollectiveDefense(org_a).publish_from_threat(
            {
                "patterns": ["prompt_injection", "tool_exfil"],
                "riskScore": 0.91,
                "riskBand": "critical",
                "recommendation": "kill",
            }
        )
        hub_a = CTIHub(org_a)
        hub_a.submit(sig, org_id="org-a")
        # B pulls via export/import of hub feed (local society primitive)
        feed = hub_a.feed_list(limit=50)
        for item in feed:
            CTIHub(org_b).submit(item, org_id="org-a")
        pulled = CollectiveDefense(org_b).list_signatures(source="inbox")
        # Also mirror into B collective inbox via import of outbox bundle
        bundle = CollectiveDefense(org_a).export_bundle()
        CollectiveDefense(org_b).import_bundle(bundle)

        cert_docker = PartnerRuntimeCertifier(org_a).certify("docker")
        cert_k8s = PartnerRuntimeCertifier(org_b).certify("kubernetes")
        mesh = CTIMesh(org_a)
        mesh.set_hubs([])  # local-only

        return {
            "mode": "local-two-org-society",
            "orgA": {
                "published": sig["signatureId"],
                "hubFeed": len(hub_a.feed_list(limit=100)),
                "dockerCert": cert_docker["level"],
            },
            "orgB": {
                "hubFeed": len(CTIHub(org_b).feed_list(limit=100)),
                "inboxViaBundle": len(CollectiveDefense(org_b).list_signatures()),
                "k8sCert": cert_k8s["level"],
            },
            "ok": cert_docker["valid"] and cert_k8s["valid"] and len(feed) >= 1,
            "standard": "NGS-0020-society",
            "note": "Society-scale = multi-org CTI + partner certs; live hubs optional",
            "pulledHint": len(pulled),
            "meshHubs": mesh.list_hubs(),
        }


def demo_hub(hub_url: str) -> dict:
    from uap.collective import CollectiveDefense
    from uap.cti_mesh import CTIMesh
    from uap.partner_cert import PartnerRuntimeCertifier

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        CollectiveDefense(ws).set_opt_in(True)
        sig = CollectiveDefense(ws).publish_from_threat(
            {
                "patterns": ["society_demo"],
                "riskScore": 0.8,
                "riskBand": "high",
                "recommendation": "contain",
            }
        )
        from uap.cti_hub import CTIHub

        CTIHub(ws).submit(sig, org_id="demo")
        mesh = CTIMesh(ws)
        mesh.set_hubs([hub_url.rstrip("/")])
        sync = mesh.sync()
        cert = PartnerRuntimeCertifier(ws).certify("docker", attested=True)
        return {
            "mode": "live-hub",
            "hub": hub_url,
            "sync": sync,
            "partnerCert": {"level": cert["level"], "valid": cert["valid"]},
            "ok": bool(sync.get("ok")) and cert["valid"],
            "standard": "NGS-0020-society",
        }


def main() -> int:
    p = argparse.ArgumentParser(description="NARNA society-scale CTI + partner cert demo")
    p.add_argument("--hub", default="", help="Optional live CTI hub base URL")
    args = p.parse_args()
    out = demo_hub(args.hub) if args.hub else demo_local()
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
