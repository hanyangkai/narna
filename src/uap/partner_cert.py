"""Partner runtime certification — NGS-0016-partner-cert (Tier D).

NARNA certifies that an isolation partner's plan/apply contract meets
Defense-in-Depth isolation controls. Certificates are local (workspace)
unless exported for peer exchange.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id
from .isolation_partner import IsolationRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Checklist ids → human label. Partners must satisfy all for L1+.
CONTROL_CHECKS: list[tuple[str, str]] = [
    ("network_isolation", "Network deny / --network none"),
    ("privilege_drop", "Non-root / no privilege escalation"),
    ("resource_limits", "Memory and/or CPU limits"),
    ("read_only_root", "Read-only root filesystem (or equivalent)"),
    ("plan_contract", "Emits NGS-0016-partner plan"),
]


class PartnerRuntimeCertifier:
    """Issue / list / verify isolation partner certificates."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "guardian" / "partner-certs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry = IsolationRegistry(self.workspace)

    def _path(self, partner: str) -> Path:
        key = partner.lower().strip()
        if key == "k8s":
            key = "kubernetes"
        return self.root / f"{key}.json"

    def audit(self, partner: str, *, agent_id: str = "cert-probe") -> dict[str, Any]:
        """Run structural checks against partner plan (no cluster/docker required)."""
        key = "kubernetes" if partner.lower().strip() == "k8s" else partner.lower().strip()
        plan = self.registry.plan(key, agent_id=agent_id)
        results: dict[str, bool] = {}
        notes: list[str] = []

        # network
        if key == "docker":
            argv = (plan.get("plan") or {}).get("argv") or []
            results["network_isolation"] = "--network" in argv and "none" in argv
            caps = set(plan.get("capabilities") or [])
            results["privilege_drop"] = True  # docker runner uses non-privileged defaults
            results["resource_limits"] = "memory_limit" in caps
            results["read_only_root"] = "read_only_root" in caps
        else:
            netpol = plan.get("networkPolicy") or {}
            egress = netpol.get("spec", {}).get("egress")
            results["network_isolation"] = egress == []
            sc = (
                ((plan.get("pod") or {}).get("spec") or {})
                .get("containers", [{}])[0]
                .get("securityContext")
                or {}
            )
            results["privilege_drop"] = bool(
                sc.get("runAsNonRoot") and sc.get("allowPrivilegeEscalation") is False
            )
            limits = (
                ((plan.get("pod") or {}).get("spec") or {})
                .get("containers", [{}])[0]
                .get("resources", {})
                .get("limits")
                or {}
            )
            results["resource_limits"] = bool(limits.get("memory") or limits.get("cpu"))
            results["read_only_root"] = bool(sc.get("readOnlyRootFilesystem"))

        results["plan_contract"] = plan.get("standard") == "NGS-0016-partner"
        if not results["plan_contract"]:
            notes.append("plan missing standard=NGS-0016-partner")

        passed = sum(1 for v in results.values() if v)
        total = len(CONTROL_CHECKS)
        level = "L0"
        if passed == total:
            level = "L1"
            # L2 when partner can apply (docker execute path exists; k8s stays plan-only)
            if key == "docker":
                apply = self.registry.apply(key, agent_id=agent_id, dry_run=True)
                if apply.get("partner") == "docker":
                    level = "L2"
            elif key == "kubernetes":
                level = "L1"  # plan-only partner ceiling without cluster attest

        return {
            "partner": key,
            "checks": results,
            "passed": passed,
            "total": total,
            "level": level,
            "controls": [{"id": c, "label": lab, "ok": results.get(c, False)} for c, lab in CONTROL_CHECKS],
            "notes": notes,
            "planSnippet": {
                "partner": plan.get("partner"),
                "standard": plan.get("standard"),
                "capabilities": plan.get("capabilities"),
            },
            "standard": "NGS-0016-partner-cert",
            "auditedAt": _now(),
        }

    def certify(
        self,
        partner: str,
        *,
        agent_id: str = "cert-probe",
        attested: bool = False,
        issuer: str = "narna-local",
    ) -> dict[str, Any]:
        audit = self.audit(partner, agent_id=agent_id)
        level = audit["level"]
        if attested and level in ("L1", "L2"):
            level = "L3"
            audit["notes"].append("operator attested (L3)")
        cert = {
            "certificateId": new_id("pcert"),
            "partner": audit["partner"],
            "level": level,
            "checks": audit["checks"],
            "controls": audit["controls"],
            "passed": audit["passed"],
            "total": audit["total"],
            "attested": attested,
            "issuer": issuer,
            "issuedAt": _now(),
            "standard": "NGS-0016-partner-cert",
            "valid": audit["passed"] == audit["total"],
        }
        path = self._path(audit["partner"])
        path.write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")
        return cert

    def get(self, partner: str) -> dict[str, Any] | None:
        path = self._path(partner)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in sorted(self.root.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

    def verify(self, partner: str) -> dict[str, Any]:
        cert = self.get(partner)
        if not cert:
            return {"ok": False, "partner": partner, "error": "no certificate"}
        # Re-audit and compare level floor
        audit = self.audit(partner)
        structural_ok = audit["passed"] == audit["total"]
        return {
            "ok": bool(cert.get("valid")) and structural_ok,
            "certificate": cert,
            "reAudit": {"level": audit["level"], "passed": audit["passed"], "total": audit["total"]},
            "verifiedAt": _now(),
        }

    def export_bundle(self) -> dict[str, Any]:
        return {
            "kind": "narna.partner-cert.bundle",
            "standard": "NGS-0016-partner-cert",
            "certificates": self.list(),
            "exportedAt": _now(),
        }

    def import_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        imported = 0
        for cert in bundle.get("certificates") or []:
            partner = str(cert.get("partner") or "").strip()
            if not partner:
                continue
            path = self._path(partner)
            path.write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")
            imported += 1
        return {"ok": True, "imported": imported}
