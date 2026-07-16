"""OTLP export bridge — NARNA runs → OpenTelemetry traces (optional SDK)."""

from __future__ import annotations

from typing import Any

from .otel import export_run_as_otel_attributes


def export_run_to_otlp(
    run_summary: dict[str, Any],
    *,
    endpoint: str | None = None,
    service_name: str = "narna-agent",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Export a NARNA run summary as an OTLP trace span.

  Requires optional ``opentelemetry-sdk`` and ``opentelemetry-exporter-otlp``.
  Falls back to attribute map when SDK is not installed.
    """
    attrs = export_run_as_otel_attributes(run_summary)
    if dry_run:
        return {"ok": True, "dryRun": True, "attributes": attrs}
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": service_name,
                "narna.agent_id": str(run_summary.get("agentId") or ""),
            }
        )
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint or "http://localhost:4318/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("narna.opentelemetry")

        with tracer.start_as_current_span("narna.run") as span:
            for k, v in attrs.items():
                if v is not None:
                    span.set_attribute(k, v)
            span.set_attribute("narna.exported", True)

        provider.force_flush()
        return {"ok": True, "endpoint": endpoint or "http://localhost:4318/v1/traces", "attributes": attrs}
    except ImportError:
        return {
            "ok": False,
            "error": "install opentelemetry-sdk and opentelemetry-exporter-otlp for OTLP export",
            "attributes": attrs,
            "hint": "pip install opentelemetry-sdk opentelemetry-exporter-otlp",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "attributes": attrs}
