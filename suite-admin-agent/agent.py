#!/usr/bin/env python3
import http.server
import json
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

HOST = os.getenv('AGENT_HOST', '0.0.0.0')
PORT = int(os.getenv('AGENT_PORT', '8079'))
TOKEN = os.getenv('ADMIN_AGENT_TOKEN', '')
SUITE_ROOT = Path(os.getenv('SUITE_ROOT', '/suite')).resolve()
UPDATES_DIR = Path(os.getenv('UPDATES_DIR', '/updates')).resolve()
LOG_DIR = UPDATES_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

JOBS = {}
JOBS_LOCK = threading.Lock()


def now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def tail(path, limit=6000):
    try:
        data = Path(path).read_text(errors='replace')
        return data[-limit:]
    except Exception:
        return ''



def human_size(num):
    try:
        num = float(num)
        for unit in ['o', 'Ko', 'Mo', 'Go', 'To']:
            if num < 1024:
                return f'{num:.1f} {unit}' if unit != 'o' else f'{int(num)} {unit}'
            num /= 1024
    except Exception:
        pass
    return str(num)


def list_backup_files():
    backups_root = (SUITE_ROOT / 'backups').resolve()
    allowed_kinds = {
        'daily': backups_root / 'daily',
        'manual': backups_root / 'manual',
        'pre_upgrade': backups_root / 'pre_upgrade',
        'pre_restore': backups_root / 'pre_restore',
    }
    items = []
    for kind, folder in allowed_kinds.items():
        if not folder.exists():
            continue
        for path in sorted(folder.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)[:50]:
            try:
                rel = str(path.resolve().relative_to(SUITE_ROOT))
                st = path.stat()
                items.append({
                    'kind': kind,
                    'path': rel,
                    'size_bytes': st.st_size,
                    'size_human': human_size(st.st_size),
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
                    'restorable': True,
                })
            except Exception:
                continue
    return items[:100]


def list_database_backup_files():
    backups_root = (SUITE_ROOT / 'backups' / 'databases').resolve()
    allowed_kinds = {
        'daily': backups_root / 'daily',
        'manual': backups_root / 'manual',
        'pre_upgrade': backups_root / 'pre_upgrade',
        'pre_restore': backups_root / 'pre_restore',
    }
    items = []
    for kind, folder in allowed_kinds.items():
        if not folder.exists():
            continue
        for path in sorted(folder.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)[:80]:
            try:
                rel = str(path.resolve().relative_to(SUITE_ROOT))
                st = path.stat()
                module = 'inconnu'
                name = path.name
                if name.startswith('lp-suite-db-'):
                    module = name.removeprefix('lp-suite-db-').rsplit('-', 2)[0]
                items.append({
                    'kind': kind,
                    'module': module,
                    'path': rel,
                    'size_bytes': st.st_size,
                    'size_human': human_size(st.st_size),
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)),
                    'restorable': True,
                })
            except Exception:
                continue
    return items[:150]

def authorized(handler):
    if not TOKEN:
        return True
    return handler.headers.get('X-Agent-Token') == TOKEN


def run_command(job_id, action, command, cwd=None):
    log_path = LOG_DIR / f'{job_id}.log'
    with JOBS_LOCK:
        JOBS[job_id]['status'] = 'running'
        JOBS[job_id]['message'] = f'Action {action} démarrée.'
        JOBS[job_id]['log_path'] = str(log_path)
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f'[{now()}] START {action}\n')
        log.write(f'Commande: {" ".join(command)}\n')
        log.flush()
        try:
            result = subprocess.run(command, cwd=str(cwd or SUITE_ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
            status = 'success' if result.returncode == 0 else 'failed'
            msg = f'Action {action} terminée.' if status == 'success' else f'Action {action} échouée avec code {result.returncode}.'
            log.write(f'[{now()}] {msg}\n')
        except Exception as exc:
            status = 'failed'
            msg = f'Exception pendant {action}: {exc}'
            log.write(f'[{now()}] {msg}\n')
    with JOBS_LOCK:
        JOBS[job_id]['status'] = status
        JOBS[job_id]['message'] = msg
        JOBS[job_id]['log_tail'] = tail(log_path)


def start_job(action, payload):
    allowed = {
        'apply_public_settings': ['bash', str(SUITE_ROOT / 'scripts/apply_public_settings.sh')],
        'issue_cert': ['bash', str(SUITE_ROOT / 'scripts/cert_manager.sh'), 'issue'],
        'renew_cert': ['bash', str(SUITE_ROOT / 'scripts/cert_manager.sh'), 'renew'],
        'cert_status': ['bash', str(SUITE_ROOT / 'scripts/cert_manager.sh'), 'status'],
        'restart_services': ['docker', 'compose', 'up', '-d', '--build'],
        'migrate_all': ['bash', str(SUITE_ROOT / 'scripts/migrate_all.sh')],
        'backup_all': ['bash', str(SUITE_ROOT / 'scripts/backup_all.sh')],
        'full_backup': ['bash', str(SUITE_ROOT / 'scripts/full_backup.sh'), 'manual'],
    }
    if action == 'backup_database':
        module = str(payload.get('module') or 'all')
        allowed_modules = {'all','lp-core','toolmag','safety','pedashop','system-manager','tpmanager','pfmp'}
        if module not in allowed_modules:
            raise ValueError('Module de sauvegarde base non autorisé.')
        command = ['bash', str(SUITE_ROOT / 'scripts/postgres/backup_database.sh'), module, 'manual']
    elif action == 'restore_database_backup':
        module = str(payload.get('module') or 'auto')
        allowed_modules = {'auto','all','lp-core','toolmag','safety','pedashop','system-manager','tpmanager','pfmp'}
        if module not in allowed_modules:
            raise ValueError('Module de restauration base non autorisé.')
        filename = Path(str(payload.get('filename', ''))).name
        backup_path = str(payload.get('backup_path', ''))
        if filename:
            if not filename.endswith('.zip'):
                raise ValueError('Nom de ZIP invalide.')
            zip_path = (UPDATES_DIR / 'incoming' / filename).resolve()
            if not str(zip_path).startswith(str(UPDATES_DIR.resolve())) or not zip_path.is_file():
                raise ValueError('Sauvegarde ZIP introuvable ou hors dossier autorisé.')
        else:
            rel = Path(backup_path)
            if not str(rel).endswith('.zip') or rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Chemin de sauvegarde base invalide.')
            zip_path = (SUITE_ROOT / rel).resolve()
            backups_root = (SUITE_ROOT / 'backups' / 'databases').resolve()
            if not str(zip_path).startswith(str(backups_root)) or not zip_path.is_file():
                raise ValueError('Sauvegarde base introuvable ou hors dossier autorisé.')
        command = ['bash', str(SUITE_ROOT / 'scripts/postgres/restore_database_backup.sh'), str(zip_path), module]
    elif action == 'install_update':
        filename = Path(str(payload.get('filename', ''))).name
        if not filename or not filename.endswith('.zip'):
            raise ValueError('Nom de ZIP invalide.')
        zip_path = (UPDATES_DIR / 'incoming' / filename).resolve()
        if not str(zip_path).startswith(str(UPDATES_DIR.resolve())) or not zip_path.is_file():
            raise ValueError('ZIP introuvable ou hors dossier autorisé.')
        command = ['bash', str(SUITE_ROOT / 'scripts/web_upgrade_from_zip.sh'), str(zip_path)]
    elif action == 'restore_full_backup':
        filename = Path(str(payload.get('filename', ''))).name
        if not filename or not filename.endswith('.zip'):
            raise ValueError('Nom de sauvegarde ZIP invalide.')
        zip_path = (UPDATES_DIR / 'incoming' / filename).resolve()
        if not str(zip_path).startswith(str(UPDATES_DIR.resolve())) or not zip_path.is_file():
            raise ValueError('Sauvegarde ZIP introuvable ou hors dossier autorisé.')
        command = ['bash', str(SUITE_ROOT / 'scripts/restore_full_backup.sh'), str(zip_path)]
    elif action == 'restore_existing_backup':
        rel = Path(str(payload.get('backup_path', '')))
        if not str(rel).endswith('.zip') or rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Chemin de sauvegarde serveur invalide.')
        zip_path = (SUITE_ROOT / rel).resolve()
        backups_root = (SUITE_ROOT / 'backups').resolve()
        if not str(zip_path).startswith(str(backups_root)) or not zip_path.is_file():
            raise ValueError('Sauvegarde serveur introuvable ou hors dossier autorisé.')
        command = ['bash', str(SUITE_ROOT / 'scripts/restore_full_backup.sh'), str(zip_path)]
    else:
        if action not in allowed:
            raise ValueError(f'Action non autorisée: {action}')
        command = allowed[action]
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {
            'job_id': job_id,
            'action': action,
            'status': 'queued',
            'message': 'Job en file d’attente.',
            'created_at': now(),
            'log_tail': '',
        }
    thread = threading.Thread(target=run_command, args=(job_id, action, command, SUITE_ROOT), daemon=True)
    thread.start()
    return JOBS[job_id]


class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body_json(self):
        length = int(self.headers.get('Content-Length', '0') or '0')
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode('utf-8'))

    def do_GET(self):
        if not authorized(self):
            return self._json(403, {'ok': False, 'error': 'Forbidden'})
        path = urlparse(self.path).path
        if path == '/health':
            return self._json(200, {'ok': True, 'suite_root': str(SUITE_ROOT), 'updates_dir': str(UPDATES_DIR)})
        if path.startswith('/jobs/'):
            job_id = path.split('/')[-1]
            with JOBS_LOCK:
                job = dict(JOBS.get(job_id) or {})
            if not job:
                return self._json(404, {'ok': False, 'error': 'Job inconnu'})
            if job.get('log_path'):
                job['log_tail'] = tail(job['log_path'])
            return self._json(200, {'ok': True, **job})
        if path == '/jobs':
            with JOBS_LOCK:
                jobs = list(JOBS.values())[-30:]
            return self._json(200, {'ok': True, 'jobs': jobs})
        if path == '/backups':
            return self._json(200, {'ok': True, 'backups': list_backup_files()})
        if path == '/database-backups':
            return self._json(200, {'ok': True, 'backups': list_database_backup_files()})
        return self._json(404, {'ok': False, 'error': 'Not found'})

    def do_POST(self):
        if not authorized(self):
            return self._json(403, {'ok': False, 'error': 'Forbidden'})
        path = urlparse(self.path).path
        if path != '/actions':
            return self._json(404, {'ok': False, 'error': 'Not found'})
        try:
            payload = self._body_json()
            action = payload.get('action')
            job = start_job(action, payload)
            return self._json(202, {'ok': True, 'job_id': job['job_id'], 'status': job['status'], 'message': job['message']})
        except Exception as exc:
            return self._json(400, {'ok': False, 'error': str(exc)})

    def log_message(self, fmt, *args):
        print(f'[{now()}] {self.address_string()} {fmt % args}', flush=True)


if __name__ == '__main__':
    print(f'suite-admin-agent listening on {HOST}:{PORT}', flush=True)
    http.server.ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
