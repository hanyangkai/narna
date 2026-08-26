"""Fullscreen TUI for NARNA Ask — optional dep: pip install 'narna[tui]' (Hermes gap P5)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .slash_commands import SLASH_CMDS, SLASH_HELP, parse_slash


def run_tui(*, provider: str | None = None, workspace: str | Path | None = None) -> int:
    try:
        from textual.app import App, ComposeResult
        from textual.binding import Binding
        from textual.widgets import Footer, Header, Input, RichLog, Static
    except ImportError:
        print(
            "textual not installed. Run: pip install 'narna[tui]'\n"
            "Or use: narna chat",
            file=sys.stderr,
        )
        return 1

    from .model_router import ModelRouter
    from .narna_agent import NarnaAgent

    ws = Path(workspace) if workspace else Path.cwd()
    router = ModelRouter(provider=provider or None)
    agent = NarnaAgent(ws, router=router)

    class NarnaTui(App[None]):
        CSS = """
        Screen { layout: vertical; }
        #status { height: 1; color: $text-muted; padding: 0 1; }
        #log { height: 1fr; border: solid $accent; margin: 0 1; padding: 0 1; }
        #input { margin: 0 1 1 1; }
        """
        BINDINGS = [
            Binding("ctrl+c", "interrupt", "Interrupt", show=True),
            Binding("ctrl+n", "new_session", "New", show=True),
            Binding("ctrl+q", "quit", "Quit", show=True),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.session_id: str | None = None
            self._busy = False
            self._partial = ""
            self._phase = "idle"

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(self._status_text(), id="status")
            yield RichLog(id="log", markup=True, wrap=True, highlight=True)
            yield Input(
                placeholder="Ask NARNA…  (/help · Tab autocomplete)",
                id="input",
            )
            yield Footer()

        def on_mount(self) -> None:
            self.title = "NARNA"
            self.sub_title = "Decision-quality agent"
            log = self.query_one("#log", RichLog)
            log.write("[bold]NARNA TUI[/] — /help · Ctrl+N new · Ctrl+C interrupt · Ctrl+Q quit")
            self.query_one("#input", Input).focus()

        def _status_text(self) -> str:
            model = router.pick_model("reason")
            return (
                f"provider={router.provider} · model={model} · "
                f"session={self.session_id or '—'} · phase={self._phase}"
            )

        def _refresh_status(self) -> None:
            self.query_one("#status", Static).update(self._status_text())

        def action_new_session(self) -> None:
            self.session_id = None
            self._phase = "idle"
            self._refresh_status()
            self.query_one("#log", RichLog).write("[dim](new session)[/]")

        def action_interrupt(self) -> None:
            if self._busy and self._partial:
                self.query_one("#log", RichLog).write(
                    f"[yellow]interrupted[/] partial: {self._partial[:500]}"
                )
            self._busy = False
            self._phase = "idle"
            self._refresh_status()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            line = (event.value or "").strip()
            event.input.value = ""
            if not line or self._busy:
                return
            self.run_worker(self._handle_line(line), exclusive=True)

        async def _handle_line(self, line: str) -> None:
            log = self.query_one("#log", RichLog)
            slash = parse_slash(line)
            if slash:
                cmd = slash["cmd"]
                arg = slash["args"]
                if cmd in {"/quit", "/exit"}:
                    self.exit()
                    return
                if cmd == "/help":
                    log.write(SLASH_HELP)
                    return
                if cmd in {"/new", "/reset"}:
                    self.action_new_session()
                    return
                if cmd == "/clear":
                    log.clear()
                    return
                if cmd == "/tools":
                    log.write(", ".join(t["name"] for t in agent.tools.specs()))
                    return
                if cmd == "/skills":
                    for s in agent.skills.list_skills()[:20]:
                        log.write(f"- {s.get('skillId')}: {s.get('name')}")
                    return
                if cmd == "/jobs":
                    for j in agent.jobs.list_jobs()[:20]:
                        log.write(
                            f"- {j.get('jobId')}: {j.get('prompt')} every={j.get('everyMinutes')}"
                        )
                    return
                if cmd == "/memory":
                    hits = agent.fts.search(arg or "decision", limit=5)
                    log.write(str(hits)[:2000])
                    return
                if cmd == "/cron":
                    from .nl_cron import parse_nl_schedule

                    try:
                        parsed = parse_nl_schedule(arg or line)
                        row = agent.jobs.create(
                            prompt=str(parsed["prompt"]),
                            every_minutes=parsed.get("everyMinutes"),
                            run_at=parsed.get("runAt"),
                            channel=str(parsed.get("channel") or "job"),
                        )
                        log.write(f"[green]job[/] {row.get('jobId')}")
                    except Exception as e:
                        log.write(f"[red]cron error:[/] {e}")
                    return
                if cmd == "/model":
                    if arg:
                        router.models = {**(router.models or {}), "reason": arg}
                        log.write(f"model={arg}")
                    else:
                        log.write(f"model={router.pick_model('reason')}")
                    self._refresh_status()
                    return
                if cmd == "/provider":
                    if arg:
                        router.provider = arg.lower()
                    log.write(f"provider={router.provider}")
                    self._refresh_status()
                    return
                log.write(f"unknown slash: {cmd} — try /help")
                return

            log.write(f"[bold cyan]you>[/] {line}")
            self._busy = True
            self._partial = ""
            self._phase = "tools"
            self._refresh_status()
            try:
                # Run Ask in a thread so UI stays responsive
                import asyncio

                out: dict[str, Any] = await asyncio.to_thread(
                    lambda: agent.ask(line, session_id=self.session_id, use_tools=True)
                )
                self.session_id = str(out.get("sessionId") or self.session_id)
                self._partial = str(out.get("answer") or "")
                self._phase = "adqa"
                self._refresh_status()
                answer = self._partial
                dqs = out.get("dqs")
                guardian = out.get("guardian")
                tools = out.get("toolsUsed") or []
                log.write(f"[bold green]narna>[/] {answer}")
                badge = f"DQS {dqs} · {guardian}"
                if tools:
                    names = ", ".join(sorted({str(t.get('tool')) for t in tools}))
                    badge += f" · tools: {names}"
                log.write(f"[dim]{badge}[/]")
            except Exception as e:
                log.write(f"[red]error:[/] {e}")
            finally:
                self._busy = False
                self._phase = "idle"
                self._refresh_status()

        def on_input_changed(self, event: Input.Changed) -> None:
            # Simple slash autocomplete: Tab completes in Input via suggestion
            val = event.value or ""
            if not val.startswith("/"):
                return
            matches = [c for c in SLASH_CMDS if c.startswith(val.lower())]
            if len(matches) == 1 and matches[0] != val.lower():
                # Show hint in status
                self.query_one("#status", Static).update(
                    self._status_text() + f" · suggest {matches[0]}"
                )

    app = NarnaTui()
    app.run()
    return 0
