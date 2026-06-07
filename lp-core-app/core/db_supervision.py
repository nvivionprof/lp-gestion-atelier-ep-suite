from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class DatabaseStatus:
    code: str
    label: str
    database: str
    engine: str
    ok: bool
    size_pretty: str = '—'
    size_bytes: int | None = None
    table_count: int | None = None
    migration_count: int | None = None
    last_migration: str = '—'
    error: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _env(name: str, default: str = '') -> str:
    return os.getenv(name, default) or default


def configured_module_databases() -> list[tuple[str, str, str]]:
    return [
        ('lp-core', 'LP Core', _env('LP_CORE_DB_NAME', _env('POSTGRES_DB', 'lp_core'))),
        ('toolmag', 'ToolMag', _env('TOOLMAG_DB_NAME', 'toolmag')),
        ('safety', 'Safety Manager', _env('SAFETY_DB_NAME', 'safety')),
        ('pedashop', 'PedaShop', _env('PEDASHOP_DB_NAME', 'pedashop')),
        ('system-manager', 'System Manager', _env('SYSTEM_MANAGER_DB_NAME', 'system_manager')),
        ('tpmanager', 'TP Manager', _env('TPMANAGER_DB_NAME', 'tpmanager')),
        ('pfmp', 'PFMP Manager', _env('PFMP_DB_NAME', 'pfmp')),
    ]


def _collect_postgresql_database(code: str, label: str, database: str) -> DatabaseStatus:
    import psycopg2

    status = DatabaseStatus(code=code, label=label, database=database, engine='postgresql', ok=False)
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=_env('POSTGRES_USER', _env('DB_USER', 'lp_suite_user')),
            password=_env('POSTGRES_PASSWORD', _env('DB_PASSWORD', '')),
            host=_env('POSTGRES_HOST', _env('DB_HOST', 'postgres')),
            port=_env('POSTGRES_PORT', _env('DB_PORT', '5432')),
            connect_timeout=3,
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT pg_database_size(current_database()), pg_size_pretty(pg_database_size(current_database()))')
            size_bytes, size_pretty = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
            table_count = cur.fetchone()[0]
            try:
                cur.execute('SELECT COUNT(*) FROM django_migrations')
                migration_count = cur.fetchone()[0]
                cur.execute('SELECT app || ''.'' || name FROM django_migrations ORDER BY applied DESC LIMIT 1')
                row = cur.fetchone()
                last_migration = row[0] if row else '—'
            except Exception:
                migration_count = 0
                last_migration = 'django_migrations absent'
        status.ok = True
        status.size_bytes = int(size_bytes)
        status.size_pretty = str(size_pretty)
        status.table_count = int(table_count)
        status.migration_count = int(migration_count)
        status.last_migration = str(last_migration)
    except Exception as exc:
        status.error = str(exc)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return status


def collect_database_supervision() -> dict[str, Any]:
    engine = _env('DB_ENGINE', 'django.db.backends.sqlite3')
    postgres_mode = 'postgresql' in engine
    databases = []
    if postgres_mode:
        for code, label, database in configured_module_databases():
            databases.append(_collect_postgresql_database(code, label, database).to_dict())
    else:
        databases.append(DatabaseStatus(
            code='local-sqlite', label='Installation SQLite', database=_env('DB_NAME', 'db.sqlite3'),
            engine=engine, ok=True, error='Supervision multi-bases disponible après bascule PostgreSQL.'
        ).to_dict())
    return {
        'engine': engine,
        'postgres_mode': postgres_mode,
        'host': _env('POSTGRES_HOST', _env('DB_HOST', 'postgres')),
        'port': _env('POSTGRES_PORT', _env('DB_PORT', '5432')),
        'user': _env('POSTGRES_USER', _env('DB_USER', 'lp_suite_user')),
        'items': databases,
        'ok_count': sum(1 for item in databases if item.get('ok')),
        'total_count': len(databases),
    }
