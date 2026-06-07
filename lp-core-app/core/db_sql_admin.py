from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render


def _database_path() -> Path:
    cfg = settings.DATABASES.get('default', {})
    engine = cfg.get('ENGINE', '')
    if 'sqlite3' not in engine:
        raise RuntimeError("Export/import SQL disponible uniquement pour SQLite dans cette version.")
    name = cfg.get('NAME')
    if not name:
        raise RuntimeError('Chemin de base SQLite introuvable.')
    return Path(str(name))


def _backup_dir(db_path: Path) -> Path:
    base = db_path.parent / 'sql_import_backups'
    base.mkdir(parents=True, exist_ok=True)
    return base


def database_context(app_label: str):
    db_path = _database_path()
    exists = db_path.exists()
    size = db_path.stat().st_size if exists else 0
    return {
        'app_label': app_label,
        'db_path': str(db_path),
        'db_exists': exists,
        'db_size': size,
        'db_size_mb': round(size / (1024 * 1024), 2),
        'engine': settings.DATABASES.get('default', {}).get('ENGINE', ''),
    }


def render_sql_admin(request, template_name: str, app_label: str):
    return render(request, template_name, database_context(app_label))


def export_sql_response(request, app_slug: str):
    db_path = _database_path()
    if not db_path.exists():
        return HttpResponseBadRequest('Base SQLite introuvable.')
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f'{app_slug}-{now}.sql'
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    try:
        lines = [
            f'-- Export SQL {app_slug}',
            f'-- Date: {now}',
            f'-- Source: {db_path}',
            'PRAGMA foreign_keys=OFF;',
            'BEGIN TRANSACTION;',
        ]
        for line in conn.iterdump():
            if line in ('BEGIN TRANSACTION;', 'COMMIT;'):
                continue
            lines.append(line)
        lines.append('COMMIT;')
        lines.append('PRAGMA foreign_keys=ON;')
        payload = '\n'.join(lines) + '\n'
    finally:
        conn.close()
    response = HttpResponse(payload, content_type='application/sql; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _make_preimport_backup(db_path: Path, app_slug: str) -> Path:
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    target = _backup_dir(db_path) / f'{app_slug}-preimport-{now}.sqlite3'
    if db_path.exists():
        shutil.copy2(db_path, target)
    else:
        target.write_bytes(b'')
    return target


def _validate_sql_to_temp(sql_text: str, db_path: Path) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix='import-', suffix='.sqlite3', dir=str(db_path.parent), delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    conn = sqlite3.connect(str(tmp_path))
    try:
        conn.executescript(sql_text)
        conn.commit()
        conn.execute('PRAGMA integrity_check;')
    finally:
        conn.close()
    return tmp_path


def import_sql_response(request, template_name: str, app_label: str, app_slug: str):
    if request.method != 'POST':
        return render_sql_admin(request, template_name, app_label)
    upload = request.FILES.get('sql_file')
    mode = request.POST.get('mode', 'replace')
    confirm = request.POST.get('confirm') == 'yes'
    if not upload:
        return HttpResponseBadRequest('Aucun fichier SQL fourni.')
    if not confirm:
        return HttpResponseBadRequest('Confirmation obligatoire avant import SQL.')
    if not upload.name.lower().endswith('.sql'):
        return HttpResponseBadRequest('Le fichier doit porter une extension .sql.')
    raw = upload.read()
    try:
        sql_text = raw.decode('utf-8')
    except UnicodeDecodeError:
        sql_text = raw.decode('utf-8', errors='replace')
    if not sql_text.strip():
        return HttpResponseBadRequest('Fichier SQL vide.')
    db_path = _database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    backup = _make_preimport_backup(db_path, app_slug)
    try:
        if mode == 'replace':
            tmp_path = _validate_sql_to_temp(sql_text, db_path)
            connections.close_all()
            if db_path.exists():
                replaced = _backup_dir(db_path) / f'{app_slug}-replaced-{datetime.now().strftime("%Y%m%d-%H%M%S")}.sqlite3'
                os.replace(db_path, replaced)
            os.replace(tmp_path, db_path)
            msg = f'Import SQL en remplacement terminé pour {app_label}. Sauvegarde pré-import : {backup}. Redémarrez le module puis lancez les migrations Django.'
        elif mode == 'additive':
            conn = sqlite3.connect(str(db_path))
            try:
                conn.executescript(sql_text)
                conn.commit()
            finally:
                conn.close()
            msg = f'Import SQL additif exécuté pour {app_label}. Sauvegarde pré-import : {backup}.'
        else:
            return HttpResponseBadRequest('Mode import inconnu.')
    except Exception as exc:
        return HttpResponseBadRequest(f'Import SQL annulé. Sauvegarde conservée : {backup}. Erreur : {exc}')
    return HttpResponse(f'<h1>Import SQL terminé</h1><p>{msg}</p><p><a href="../">Retour</a></p>', content_type='text/html; charset=utf-8')
