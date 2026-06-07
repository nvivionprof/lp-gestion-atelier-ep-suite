#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 CLE VALEUR" >&2
  exit 1
fi

ENV_FILE=".env"
[ -f "$ENV_FILE" ] || cp .env.example "$ENV_FILE"

KEY="$1" VALUE="$2" ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ['ENV_FILE'])
key = os.environ['KEY']
value = os.environ['VALUE']
lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
out = []
found = False

for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith('#') and '=' in stripped:
        current_key = stripped.split('=', 1)[0].strip()
        if current_key == key:
            out.append(f'{key}={value}')
            found = True
            continue
    out.append(line)

if not found:
    out.append(f'{key}={value}')
path.write_text('\n'.join(out) + '\n', encoding='utf-8')
PY
