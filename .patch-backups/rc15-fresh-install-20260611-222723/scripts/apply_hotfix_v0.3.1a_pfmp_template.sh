#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGET="pfmp-app/pfmp_manager/templates/pfmp_manager/dashboard.html"
if [[ ! -f "$TARGET" ]]; then
  echo "ERREUR : fichier introuvable : $TARGET" >&2
  exit 1
fi

if grep -q "{% endblock %}" "$TARGET"; then
  echo "OK : le dashboard PFMP contient déjà {% endblock %}."
else
  echo "Ajout de {% endblock %} à $TARGET"
  printf '\n{% endblock %}\n' >> "$TARGET"
fi

echo "Contrôle rapide des blocs Django PFMP..."
python3 - <<'PY'
from pathlib import Path
base = Path('pfmp-app/pfmp_manager/templates/pfmp_manager')
errors = []
for f in sorted(base.glob('*.html')):
    s = f.read_text(encoding='utf-8')
    b = s.count('{% block')
    e = s.count('{% endblock')
    if b != e:
        errors.append((str(f), b, e))
if errors:
    for path, b, e in errors:
        print(f'ERREUR template: {path} block={b} endblock={e}')
    raise SystemExit(1)
print('OK : blocs Django PFMP cohérents.')
PY

echo "Hotfix PFMP template appliqué. Redémarrage conseillé :"
echo "  docker compose restart pfmp-app lp-gateway"
