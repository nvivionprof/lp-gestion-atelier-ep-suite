#!/usr/bin/env python3
"""LP Gestion Atelier EP Suite - gestionnaire de versions.

Règle projet :
- install : aucune version installée.
- update  : Vx.y.z -> Vx.y.(z+n) ou RC -> finale de même version.
- upgrade : Vx.y.z -> Vx.(y+n).0.
- major   : Vx.y.z -> V(x+n).0.0.
- noop    : version cible <= version installée.

Le suffixe -RCn est inférieur à la version finale correspondante :
V0.0.1-RC6 < V0.0.1.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "versions" / "migration-policy.json"
REGISTRY_FILE = ROOT / "versions" / "version-registry.json"

def parse(v: str | None) -> tuple[int, int, int, int, int] | None:
    """Return (major, minor, patch, stage_rank, rc_number).

    stage_rank: 0=RC, 1=final. This keeps RC lower than final.
    """
    if not v or v.strip().lower() in {"unknown", "none", "null", ""}:
        return None
    raw = v.strip().upper()
    m = re.search(r"V?\s*(\d+)\.(\d+)\.(\d+)", raw)
    if not m:
        nums = re.findall(r"\d+", raw)
        if not nums:
            return None
        nums = [int(x) for x in nums[:3]]
        while len(nums) < 3:
            nums.append(0)
        major, minor, patch = nums
    else:
        major, minor, patch = map(int, m.groups())
    rc = re.search(r"(?:-|\+)?RC\s*([0-9]+)?", raw)
    if rc:
        return (major, minor, patch, 0, int(rc.group(1) or 0))
    return (major, minor, patch, 1, 0)

def numeric(v: str | None) -> tuple[int, int, int] | None:
    p = parse(v)
    if p is None:
        return None
    return p[:3]

def norm(v: str | None) -> str:
    p = parse(v)
    if p is None:
        return "unknown"
    base = f"V{p[0]}.{p[1]}.{p[2]}"
    if p[3] == 0:
        return f"{base}-RC{p[4] or 1}"
    return base

def classify(current: str | None, target: str | None) -> str:
    c = parse(current)
    t = parse(target)
    if t is None:
        return "error"
    if c is None:
        return "install"
    if t <= c:
        return "noop"
    cn = c[:3]
    tn = t[:3]
    if tn[0] == cn[0] and tn[1] == cn[1] and (tn[2] > cn[2] or (tn[2] == cn[2] and t > c)):
        return "update"
    if tn[0] == cn[0] and tn[1] > cn[1]:
        return "upgrade"
    if tn[0] > cn[0]:
        return "major_release"
    return "upgrade"

def policy() -> dict:
    if POLICY_FILE.exists():
        return json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    return {}

def registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {}

def check_allowed(mode: str, current: str | None, target: str | None) -> int:
    if mode == "install":
        print(f"Chemin install accepté : nouvelle installation vers {norm(target)}.")
        return 0
    c = parse(current)
    if c is None:
        print("ERREUR : aucune version installée détectée. Utiliser --mode install.", file=sys.stderr)
        return 2
    p = policy()
    minv = p.get(mode, {}).get("minimum_source_version")
    if minv and c[:3] < (numeric(minv) or (0,0,0)):
        print(f"ERREUR : {mode} impossible depuis {norm(current)}. Version minimale : {minv}.", file=sys.stderr)
        return 2
    print(f"Chemin {mode} accepté : {norm(current)} -> {norm(target)}.")
    return 0

def print_table() -> None:
    r = registry()
    print("LP Gestion Atelier EP Suite - politique de versions")
    print(f"Version courante : {r.get('current_version', norm((ROOT/'VERSION').read_text().strip() if (ROOT/'VERSION').exists() else 'unknown'))}")
    print("update  : Vx.y.z -> Vx.y.(z+1) ou Vx.y.z-RCn -> Vx.y.z")
    print("upgrade : Vx.y.z -> Vx.(y+1).0")
    print("major   : Vx.y.z -> V(x+1).0.0")
    print()
    print("Versions connues :")
    for rel in r.get("releases", []):
        print(f"- {rel.get('version')} | {rel.get('type')} | {rel.get('notes', '')}")


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "table"
    if cmd == "classify":
        current = argv[2] if len(argv) > 2 else None
        target = argv[3] if len(argv) > 3 else None
        print(classify(current, target))
        return 0
    if cmd == "mode":
        current = argv[2] if len(argv) > 2 else None
        target = argv[3] if len(argv) > 3 else None
        result = classify(current, target)
        print("upgrade" if result == "major_release" else result)
        return 0
    if cmd == "check":
        mode = argv[2] if len(argv) > 2 else "update"
        current = argv[3] if len(argv) > 3 else None
        target = argv[4] if len(argv) > 4 else ((ROOT / "VERSION").read_text().strip() if (ROOT / "VERSION").exists() else None)
        return check_allowed(mode, current, target)
    if cmd == "norm":
        print(norm(argv[2] if len(argv) > 2 else None))
        return 0
    if cmd in {"table", "show", "versions"}:
        print_table()
        return 0
    print("Usage: version_manager.py [table|classify CURRENT TARGET|mode CURRENT TARGET|check MODE CURRENT TARGET|norm VERSION]", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
