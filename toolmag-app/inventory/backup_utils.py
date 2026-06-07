import os
import shutil
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.utils import timezone


@dataclass
class BackupInfo:
    name: str
    path: Path
    size: int
    created_ts: float
    backup_type: str

    @property
    def created_at(self):
        return timezone.datetime.fromtimestamp(self.created_ts, tz=timezone.get_current_timezone())

    @property
    def size_mb(self):
        return round(self.size / (1024 * 1024), 2)


def backup_dir(path=None) -> Path:
    p = Path(path or os.getenv('BACKUP_DIR') or (settings.BASE_DIR / 'backups'))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _prefix_for_type(backup_type: str) -> str:
    if backup_type == 'manual':
        return 'manual-toolmag'
    if backup_type == 'pre_restore':
        return 'pre-restore-toolmag'
    return 'auto-toolmag'


def detect_backup_type(filename: str) -> str:
    if filename.startswith('manual-toolmag-'):
        return 'manual'
    if filename.startswith('pre-restore-toolmag-'):
        return 'pre_restore'
    if filename.startswith('auto-toolmag-'):
        return 'auto'
    if filename.startswith('toolmag-backup-'):
        return 'auto'
    return 'unknown'


def list_backups(path=None) -> list[BackupInfo]:
    bd = backup_dir(path)
    infos = []
    for p in sorted(bd.glob('*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True):
        infos.append(BackupInfo(
            name=p.name,
            path=p,
            size=p.stat().st_size,
            created_ts=p.stat().st_mtime,
            backup_type=detect_backup_type(p.name),
        ))
    return infos


def safe_backup_path(name: str, path=None) -> Path:
    # Empêche les traversées de chemin. On accepte uniquement un nom de fichier présent dans BACKUP_DIR.
    clean = Path(name).name
    candidate = backup_dir(path) / clean
    if not candidate.exists() or not candidate.is_file() or candidate.suffixes[-2:] != ['.tar', '.gz']:
        raise FileNotFoundError(f'Sauvegarde introuvable : {clean}')
    return candidate


def create_backup(backup_type='auto', backup_dir_path=None, retain_days=7, note='') -> Path:
    bd = backup_dir(backup_dir_path)
    stamp = timezone.localtime().strftime('%Y%m%d-%H%M%S')
    prefix = _prefix_for_type(backup_type)
    archive_path = bd / f'{prefix}-{stamp}.tar.gz'
    temp_dir = Path(tempfile.mkdtemp(prefix=f'.tmp-{stamp}-', dir=str(bd)))
    try:
        db = settings.DATABASES['default']
        engine = db.get('ENGINE', '')
        if 'sqlite3' in engine:
            db_path = Path(db.get('NAME'))
            if db_path.exists():
                shutil.copy2(db_path, temp_dir / 'db.sqlite3')
            else:
                (temp_dir / 'DB_MISSING.txt').write_text(f'Base SQLite introuvable : {db_path}\n', encoding='utf-8')
        else:
            (temp_dir / 'POSTGRES_BACKUP_NOTE.txt').write_text(
                'Base non SQLite détectée. Configurer pg_dump dans la version production.\n', encoding='utf-8'
            )
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            shutil.copytree(media_root, temp_dir / 'media', dirs_exist_ok=True)
        version = Path(settings.BASE_DIR) / 'VERSION.txt'
        if version.exists():
            shutil.copy2(version, temp_dir / 'VERSION.txt')
        metadata = {
            'type': backup_type,
            'created_at': timezone.localtime().isoformat(),
            'note': note or '',
            'toolmag_version': version.read_text(encoding='utf-8').strip() if version.exists() else '',
        }
        (temp_dir / 'BACKUP_METADATA.txt').write_text('\n'.join(f'{k}: {v}' for k, v in metadata.items()) + '\n', encoding='utf-8')
        with tarfile.open(archive_path, 'w:gz') as tar:
            for item in temp_dir.iterdir():
                tar.add(item, arcname=item.name)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    if backup_type == 'auto':
        cleanup_auto_backups(bd, retain_days)
    return archive_path


def cleanup_auto_backups(path=None, retain_days=7) -> list[str]:
    bd = backup_dir(path)
    cutoff = time.time() - int(retain_days) * 86400
    removed = []
    # On ne supprime que les sauvegardes automatiques, jamais les manuelles ni les pre_restore.
    for pattern in ('auto-toolmag-*.tar.gz', 'toolmag-backup-*.tar.gz'):
        for item in bd.glob(pattern):
            if item.stat().st_mtime < cutoff:
                removed.append(item.name)
                item.unlink(missing_ok=True)
    return removed


def restore_backup_from_archive(name: str, *, backup_dir_path=None, create_pre_restore=True, actor_label='') -> tuple[Path | None, str]:
    archive_path = safe_backup_path(name, backup_dir_path)
    pre_restore_path = None
    if create_pre_restore:
        pre_restore_path = create_backup('pre_restore', backup_dir_path=backup_dir_path, retain_days=7, note=f'Avant restauration de {archive_path.name} par {actor_label}')
    bd = backup_dir(backup_dir_path)
    extract_dir = Path(tempfile.mkdtemp(prefix='.restore-', dir=str(bd)))
    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            # Protection minimale contre extraction hors dossier temporaire.
            for member in tar.getmembers():
                target = extract_dir / member.name
                if not str(target.resolve()).startswith(str(extract_dir.resolve())):
                    raise RuntimeError(f'Chemin dangereux dans l’archive : {member.name}')
            tar.extractall(extract_dir)
        restored_parts = []
        db_file = extract_dir / 'db.sqlite3'
        if db_file.exists():
            db = settings.DATABASES['default']
            if 'sqlite3' not in db.get('ENGINE', ''):
                raise RuntimeError('Restauration web actuellement prévue pour SQLite uniquement.')
            db_path = Path(db.get('NAME'))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_file, db_path)
            restored_parts.append('base SQLite')
        media_src = extract_dir / 'media'
        if media_src.exists():
            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                shutil.rmtree(media_root)
            shutil.copytree(media_src, media_root)
            restored_parts.append('media')
        if not restored_parts:
            raise RuntimeError('Archive sans base ni dossier media exploitable.')
        return pre_restore_path, ', '.join(restored_parts)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
