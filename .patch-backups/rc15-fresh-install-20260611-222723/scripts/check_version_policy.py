#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
vm = root / 'scripts' / 'version_manager.py'
mode = sys.argv[1] if len(sys.argv) > 1 else 'update'
current = sys.argv[2] if len(sys.argv) > 2 else 'unknown'
target = (root / 'VERSION').read_text(encoding='utf-8').strip() if (root / 'VERSION').exists() else 'unknown'
raise SystemExit(subprocess.call([sys.executable, str(vm), 'check', mode, current, target]))
