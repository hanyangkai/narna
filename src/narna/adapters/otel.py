"""narna-opentelemetry — Read OTel spans into NARNA evidence hints (optional dep)."""

from __future__ import annotations

from typing import Any

from .base import AdapterResult, BaseAdapter


class OpenTelemetryAdapter(BaseAdapter):
    id = "opentelemetry"
    package = "narna-opentelemetry"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        return "opentelemetry" in mod or type(obj).__name__ in {"Tracer", "TracerProvider", "Span"}

    def attach(self, agent: Any, foreign: Any) -> AdapterResult:
        hooks: list[str] = []
        # Soft integrate: if tracer has start_as_current_span, wrap it
        if self._wrap_method(foreign, "start_as_current_span", agent):
            hooks.append("start_as_current_span")
        if self._wrap_method(foreign, "start_span", agent):
            hooks.append("start_span")
        agent._otel = {
            "linked": True,
            "note": "NARNA records runs alongside OTel — does not replace exporters.",
        }
        return AdapterResult(
            framework=self.id,
            package=self.package,
            status="available",
            hooks=hooks,
            message="Works with OpenTelemetry. NARNA owns Evidence+Trust; OTel owns spans.",
        )


def export_run_as_otel_attributes(run_summary: dict[str, Any]) -> dict[str, Any]:
    """Map a NARNA run summary to OTel-like attributes (no hard dependency)."""
    return {
        "narna.agent_id": run_summary.get("agentId"),
        "narna.run_id": run_summary.get("runId"),
        "narna.trust_score": run_summary.get("trustScore"),
        "narna.passport_id": run_summary.get("passportId"),
        "narna.constitution_id": run_summary.get("constitutionId"),
    }
