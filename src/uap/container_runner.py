"""Optional Docker Agent Container runner — host isolation hook (NGS-0016)."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


DEFAULT_IMAGE = "narna/agent-container:0.1"


class DockerContainerRunner:
    """Generate / optionally execute docker run for Agent Container policy."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def docker_available(self) -> bool:
        return shutil.which("docker") is not None

    def plan(
        self,
        *,
        agent_id: str = "agent",
        image: str = DEFAULT_IMAGE,
        network: str = "none",
        memory: str = "512m",
        cpus: str = "1",
        command: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a docker run argv matching deny-by-default network + quotas."""
        from .container import AgentContainer

        try:
            profile = AgentContainer(self.workspace).profile(agent_id)
        except FileNotFoundError:
            AgentContainer(self.workspace).install_default()
            profile = AgentContainer(self.workspace).profile(agent_id)

        net = network
        if str((profile.get("network") or "")).startswith("deny"):
            net = "none"
        ws_mount = str(self.workspace.resolve())
        argv = [
            "docker",
            "run",
            "--rm",
            "--name",
            f"narna-{agent_id}"[:60],
            "--network",
            net,
            "--memory",
            memory,
            "--cpus",
            cpus,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "-v",
            f"{ws_mount}:/workspace:rw",
            "-e",
            f"NARNA_AGENT_ID={agent_id}",
            "-e",
            "NARNA_GUARDIAN=1",
            "-w",
            "/workspace",
            image,
        ]
        if command:
            argv.extend(command)
        else:
            argv.extend(["python", "-c", "print('narna agent container ready')"])

        return {
            "ok": True,
            "argv": argv,
            "command": " ".join(argv),
            "profile": profile,
            "hostIsolation": True,
            "note": "Requires Docker on host. --network none enforces deny-by-default.",
            "standard": "NGS-0016",
            "plannedAt": _now(),
        }

    def run(self, *, dry_run: bool = True, **kwargs: Any) -> dict[str, Any]:
        plan = self.plan(**kwargs)
        if dry_run or not self.docker_available():
            plan["executed"] = False
            plan["dryRun"] = True
            if not self.docker_available():
                plan["dockerMissing"] = True
            return plan
        proc = subprocess.run(plan["argv"], capture_output=True, text=True, timeout=120)
        plan["executed"] = True
        plan["dryRun"] = False
        plan["exitCode"] = proc.returncode
        plan["stdout"] = (proc.stdout or "")[:2000]
        plan["stderr"] = (proc.stderr or "")[:2000]
        return plan

    def dockerfile_hint(self) -> str:
        return (Path(__file__).resolve().parents[2] / "web" / "deploy" / "selfhost" / "Dockerfile.agent-container").as_posix()
