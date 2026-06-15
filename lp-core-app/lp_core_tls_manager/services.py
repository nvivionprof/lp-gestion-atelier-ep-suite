import os
import subprocess
from pathlib import Path
from typing import Tuple


ROOT_DIR = Path(os.environ.get("SUITE_HOST_ROOT") or os.getcwd())
SCRIPTS_DIR = Path(os.environ.get("LP_TLS_SCRIPTS_DIR") or (ROOT_DIR / "scripts"))


def run_script(script_name: str, env_extra: dict | None = None, timeout: int = 900) -> Tuple[bool, str]:
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        return False, f"Script introuvable : {script}"

    env = os.environ.copy()
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items() if v is not None})

    try:
        proc = subprocess.run(
            [str(script)],
            cwd=str(ROOT_DIR),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode == 0, output.strip()
    except subprocess.TimeoutExpired as exc:
        return False, f"Timeout pendant l'exécution de {script_name}: {exc}"


def tls_status() -> Tuple[bool, str]:
    return run_script("tls-status.sh", timeout=60)


def duckdns_issue(token: str, cfg) -> Tuple[bool, str]:
    return run_script(
        "tls-duckdns-issue.sh",
        env_extra={
            "DUCKDNS_TOKEN": token,
            "DUCKDNS_DOMAIN": cfg.duckdns_domain,
            "DUCKDNS_FULL_DOMAIN": cfg.duckdns_full_domain,
            "TLS_EMAIL": cfg.tls_email,
            "ACME_DNS_SLEEP": cfg.acme_dns_sleep,
        },
        timeout=1200,
    )


def duckdns_renew(token: str, cfg) -> Tuple[bool, str]:
    return run_script(
        "tls-duckdns-renew.sh",
        env_extra={
            "DUCKDNS_TOKEN": token,
            "DUCKDNS_DOMAIN": cfg.duckdns_domain,
            "DUCKDNS_FULL_DOMAIN": cfg.duckdns_full_domain,
        },
        timeout=1200,
    )
