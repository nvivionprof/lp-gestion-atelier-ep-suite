#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(pwd)"
[ -f "install.sh" ] || { echo "ERREUR : lancer ce script à la racine du dépôt LP Gestion Atelier EP Suite." >&2; exit 1; }
[ -f "docker-compose.yml" ] || { echo "ERREUR : docker-compose.yml introuvable." >&2; exit 1; }

log(){ echo "[V0.0.1-RC3] $*"; }

log "Correction technique des 3 points résiduels RC2"

python3 - <<'PY'
from pathlib import Path
import json
import re

# -----------------------------------------------------------------------------
# 1) load_demo_data.sh : ne plus tenter les sync par docker compose exec avant
#    le démarrage final des services pendant ./install.sh.
# -----------------------------------------------------------------------------
load_demo = Path('scripts/load_demo_data.sh')
text = load_demo.read_text(encoding='utf-8')
old = '''log "Synchronisation post-démo vers les modules"
for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  exec_manage "$svc" sync_lp_core_users || true
done
log "Chargement démo terminé."
'''
new = '''if [ "$FROM_INSTALL" = "1" ]; then
  log "Synchronisation post-démo différée : elle sera exécutée après le démarrage final des services par install.sh."
else
  log "Synchronisation post-démo vers les modules"
  for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
    exec_manage "$svc" sync_lp_core_users || true
  done
fi
log "Chargement démo terminé."
'''
if old not in text:
    # Variante plus souple au cas où le libellé aurait changé légèrement.
    text2 = re.sub(
        r'log "Synchronisation post-démo[^\n]*"\nfor svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do\n\s*exec_manage "\$svc" sync_lp_core_users \|\| true\ndone\nlog "Chargement démo terminé\."\n',
        new,
        text,
        flags=re.S,
    )
    if text2 == text:
        raise SystemExit('Bloc de synchronisation post-démo introuvable dans scripts/load_demo_data.sh')
    text = text2
else:
    text = text.replace(old, new)
load_demo.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) tp_manager/sync.py : synchronisation utilisateurs idempotente.
#    On recherche d'abord par core_user_id, puis par code, puis par username.
#    Cela évite les erreurs UNIQUE sur PROF-0001 quand une seed a déjà créé
#    l'utilisateur avant la synchronisation LP Core.
# -----------------------------------------------------------------------------
sync_path = Path('tpmanager-app/tp_manager/sync.py')
sync_text = sync_path.read_text(encoding='utf-8')
start = sync_text.index('def sync_users_from_lp_core')
end = sync_text.index('\ndef sync_formations_from_lp_core', start)
new_func = r'''def sync_users_from_lp_core(timeout=90, force_password=False, core_user_id=None):
    api_url = settings.LP_CORE_API_URL.rstrip('/')
    url = f'{api_url}/api/users/{core_user_id}/' if core_user_id else f'{api_url}/api/users/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    data = [payload] if core_user_id else payload.get('results', [])
    report = {'created': 0, 'updated': 0, 'formations_created': 0, 'formations_updated': 0, 'errors': []}
    now = timezone.now()
    for item in data:
        try:
            formation_code = item.get('formation_code') or ''
            formation_name = item.get('formation_name') or formation_code
            if formation_code:
                formation, f_created = Formation.objects.get_or_create(code=formation_code, defaults={'nom': formation_name or formation_code})
                formation.nom = formation_name or formation.code
                formation.active = True
                formation.save()
                report['formations_created' if f_created else 'formations_updated'] += 1

            core_id = item.get('id')
            code = item.get('code') or item.get('username')
            username = item.get('username') or code

            # Idempotence renforcée : les versions précédentes pouvaient créer un
            # utilisateur par seed locale, puis essayer d'en créer un second par
            # core_user_id avec le même code. On rapproche maintenant l'existant.
            obj = None
            if core_id is not None:
                obj = TpUser.objects.filter(core_user_id=core_id).first()
            if obj is None and code:
                obj = TpUser.objects.filter(code=code).first()
            if obj is None and username:
                obj = TpUser.objects.filter(username=username).first()

            created = False
            if obj is None:
                obj = TpUser(core_user_id=core_id, code=code, username=username)
                created = True
            elif core_id is not None and not obj.core_user_id:
                obj.core_user_id = core_id

            obj.code = code
            obj.username = username
            obj.first_name = item.get('first_name') or ''
            obj.last_name = item.get('last_name') or ''
            obj.email = item.get('email') or ''
            obj.formation_code = formation_code
            obj.formation_name = formation_name or ''
            obj.class_name = item.get('class_name') or ''
            obj.group_name = item.get('group_name') or ''
            obj.role_principal = item.get('role_principal') or 'utilisateur'
            obj.rights = item.get('rights') or ''
            obj.active = bool(item.get('active', True))
            obj.school_year = item.get('school_year') or ''
            obj.synced_at = now
            initial_password = item.get('initial_password') or ''
            if initial_password and (created or force_password or settings.TPMANAGER_RESET_PASSWORDS_ON_SYNC):
                obj.set_password(initial_password)
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('username') or item.get('code')}: {exc}")
    return report

'''
sync_text = sync_text[:start] + new_func + sync_text[end+1:]
sync_path.write_text(sync_text, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) sync_system_manager : rendre l'appel non bloquant et tester les deux routes
#    internes possibles avec/sans APP_URL_PREFIX. L'installation ne doit plus
#    afficher de traceback si System Manager n'expose pas encore l'API attendue.
# -----------------------------------------------------------------------------
sync_text = sync_path.read_text(encoding='utf-8')
start = sync_text.index('def sync_systems_from_system_manager')
new_func = r'''def sync_systems_from_system_manager(timeout=30):
    base = settings.SYSTEM_MANAGER_API_URL.rstrip('/')
    candidates = [f'{base}/api/systems/']
    if not base.endswith('/system'):
        candidates.append(f'{base}/system/api/systems/')

    response = None
    last_error = None
    for url in candidates:
        try:
            response = requests.get(url, headers=_headers(), timeout=timeout, allow_redirects=False)
            if response.status_code in {301, 302, 303, 307, 308}:
                last_error = f'{url} redirige vers {response.headers.get("Location", "destination inconnue")}'
                continue
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = str(exc)
            response = None
    else:
        return {'created': 0, 'updated': 0, 'errors': [f'API System Manager indisponible : {last_error or "aucune réponse"}']}

    data = response.json().get('results', [])
    report = {'created': 0, 'updated': 0, 'errors': []}
    now = timezone.now()
    for item in data:
        try:
            code = item.get('code') or str(item.get('id'))
            obj = None
            if item.get('id') is not None:
                obj = SystemePedagogiqueRef.objects.filter(system_manager_id=item.get('id')).first()
            if obj is None:
                obj = SystemePedagogiqueRef.objects.filter(code=code).first()
            created = False
            if obj is None:
                obj = SystemePedagogiqueRef(system_manager_id=item.get('id'), code=code, designation=item.get('designation') or code)
                created = True
            elif item.get('id') is not None and not obj.system_manager_id:
                obj.system_manager_id = item.get('id')
            obj.code = code
            obj.designation = item.get('designation') or code
            obj.zone_code = item.get('zone_code') or ''
            obj.zone_nom = item.get('zone_nom') or ''
            obj.statut = item.get('statut') or ''
            obj.actif = bool(item.get('actif', True))
            obj.synced_at = now
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('code')}: {exc}")
    return report
'''
sync_text = re.sub(r'def sync_systems_from_system_manager\(timeout=30\):.*\Z', new_func, sync_text, flags=re.S)
sync_path.write_text(sync_text, encoding='utf-8')

cmd_path = Path('tpmanager-app/tp_manager/management/commands/sync_system_manager.py')
cmd_text = cmd_path.read_text(encoding='utf-8')
cmd_path.write_text('''from django.core.management.base import BaseCommand\nfrom tp_manager.sync import sync_systems_from_system_manager\n\n\nclass Command(BaseCommand):\n    help = 'Synchronise les systèmes depuis System Manager vers TP Manager.'\n\n    def handle(self, *args, **options):\n        report = sync_systems_from_system_manager()\n        errors = report.get('errors') or []\n        if errors:\n            self.stdout.write(self.style.WARNING(f'Synchronisation System Manager partielle/non bloquante : {report}'))\n        else:\n            self.stdout.write(self.style.SUCCESS(f'Systèmes synchronisés : {report}'))\n''', encoding='utf-8')

# -----------------------------------------------------------------------------
# Version : RC technique suivante avant tag final V0.0.1.
# -----------------------------------------------------------------------------
version = 'V0.0.1-RC3'
for name in ['VERSION', 'VERSION.txt', '.suite-target-version']:
    p = Path(name)
    if p.exists():
        p.write_text(version + '\n', encoding='utf-8')

manifest = Path('manifest.json')
if manifest.exists():
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['version'] = version
        data['suite_version'] = version
        data['name'] = 'LP Gestion Atelier EP Suite — V0.0.1-RC3 corrections techniques post-RC2'
        data['release_stage'] = 'RC3'
        data['rc_status'] = 'release_candidate'
        data.setdefault('changes', [])
        additions = [
            'RC3 : suppression de la synchronisation post-démo trop précoce pendant install.sh.',
            'RC3 : synchronisation TP Manager idempotente sur les utilisateurs déjà créés par seed.',
            'RC3 : synchronisation System Manager vers TP Manager non bloquante et sans traceback pendant l’installation.'
        ]
        for item in additions:
            if item not in data['changes']:
                data['changes'].insert(0, item)
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except Exception as exc:
        print(f'Avertissement manifest.json non mis à jour : {exc}')
PY

log "Contrôle syntaxe Python ciblé"
python3 -m py_compile tpmanager-app/tp_manager/sync.py tpmanager-app/tp_manager/management/commands/sync_system_manager.py

log "Contrôle syntaxe Bash ciblé"
bash -n scripts/load_demo_data.sh

log "Recalcul CHECKSUMS.sha256 sans auto-référence"
find . \
  -path './.git' -prune -o \
  -path './backups' -prune -o \
  -path './postgres-db' -prune -o \
  -path './lp-core-db' -prune -o \
  -path './toolmag-db' -prune -o \
  -path './safety-db' -prune -o \
  -path './pedashop-db' -prune -o \
  -path './system-manager-db' -prune -o \
  -path './tpmanager-db' -prune -o \
  -path './pfmp-db' -prune -o \
  -path './updates' -prune -o \
  -path './logs' -prune -o \
  -type f ! -name 'CHECKSUMS.sha256' -print0 \
  | sort -z \
  | xargs -0 sha256sum > CHECKSUMS.sha256

log "Vérification checksums"
sha256sum -c CHECKSUMS.sha256 >/tmp/lp-suite-rc3-checksums.log 2>&1 || { tail -40 /tmp/lp-suite-rc3-checksums.log; exit 1; }

log "Correctifs V0.0.1-RC3 appliqués. Suite : git diff --stat, commit, push, tag, réinstallation test."
