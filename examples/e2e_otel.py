"""E2E stub — OpenTelemetry tracer wrap."""

from pathlib import Path

from narna import wrap


def main() -> None:
    ws = Path(__file__).resolve().parent / "_demo_otel"
    ws.mkdir(exist_ok=True)

    class FakeTracer:
        def start_as_current_span(self, name: str):
            class _Span:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

            return _Span()

    FakeTracer.__module__ = "opentelemetry.trace"
    agent = wrap(FakeTracer(), workspace=ws, vap=False, mode="observe")
    assert agent._adapter["package"] == "narna-opentelemetry"
    with agent._wrapped.start_as_current_span("agent.run"):
        pass
    print("e2e_otel: PASS", agent._adapter)


if __name__ == "__main__":
    main()
