"""Service health and the allow-listed control actions. Every action uses the bot's own mechanism."""
import os
import subprocess

import httpx


def _run(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout or r.stderr).strip()


def unit_state(kind: str, name: str) -> str:
    if kind == "systemd":
        return _run(["systemctl", "is-active", name], 5)[1] or "unknown"
    ok, out = _run(["docker", "inspect", "-f", "{{.State.Status}}", name], 5)
    return out if ok else "unknown"


def service_states(s) -> dict:
    return {bot: unit_state(kind, name) for bot, (kind, name) in s.services.items()}


def forex_stop(s) -> tuple[bool, str]:
    path = os.path.join(s.forex_dir, "STOP")
    if os.path.exists(path):
        return True, "STOP file already present"
    # O_EXCL: create only, never truncate or overwrite anything
    os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
    return True, f"created {path}; bot flattens and shuts down within ~10 s"


def restart(s, target: str) -> tuple[bool, str]:
    if target not in s.restart_targets:
        raise KeyError(target)
    kind, name = s.restart_targets[target]
    cmd = ["sudo", "-n", "systemctl", "restart", name] if kind == "systemd" else ["docker", "restart", name]
    ok, out = _run(cmd, 60)
    return ok, out or f"restarted {name}"


def polymarket(s, cmd: str) -> tuple[bool, str]:
    assert cmd in ("pause", "resume")
    return _run([s.hermes_bin, "cron", cmd, s.poly_cron_job])


def futures(s, cmd: str) -> tuple[bool, str]:
    assert cmd in ("pause", "resume")
    if not s.assettrade_api_key:
        return False, "ASSETTRADE_API_KEY not configured"
    try:
        r = httpx.post(f"{s.futures_api}/v1/commands/{cmd}", params={"mode": "paper"},
                       headers={"X-Api-Key": s.assettrade_api_key}, timeout=5)
    except httpx.HTTPError as e:
        return False, str(e)
    return r.status_code == 200, r.text[:300]
