"""Réparations de schéma PFMP pour les migrations RC16/RC17.

Objectif : éviter les interventions SQL manuelles lorsque la migration RC16 a été
partiellement appliquée avant d'être enregistrée dans django_migrations.
"""
from django.db import connection


def _log(stdout, msg):
    if stdout:
        stdout.write(str(msg))


def _table_exists(table_name: str) -> bool:
    with connection.cursor() as cursor:
        return table_name in connection.introspection.table_names(cursor)


def _column_exists(table_name: str, column_name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
            LIMIT 1
            """,
            [table_name, column_name],
        )
        return cursor.fetchone() is not None


def _index_exists(index_name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname = %s
            LIMIT 1
            """,
            [index_name],
        )
        return cursor.fetchone() is not None


def _migration_applied(app: str, name: str) -> bool:
    if not _table_exists('django_migrations'):
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM django_migrations WHERE app=%s AND name=%s LIMIT 1",
            [app, name],
        )
        return cursor.fetchone() is not None


def _mark_migration(app: str, name: str):
    if not _table_exists('django_migrations'):
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO django_migrations(app, name, applied)
            SELECT %s, %s, NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM django_migrations WHERE app=%s AND name=%s
            )
            """,
            [app, name, app, name],
        )


def _create_model_if_missing(editor, model, stdout=None):
    table = model._meta.db_table
    if _table_exists(table):
        _log(stdout, f"Table déjà présente : {table}")
        return False
    _log(stdout, f"Création table manquante : {table}")
    editor.create_model(model)
    return True


def _add_field_if_missing(editor, model, field_name: str, stdout=None):
    field = model._meta.get_field(field_name)
    table = model._meta.db_table
    column = getattr(field, 'column', None)
    if not column:
        return False
    if _column_exists(table, column):
        _log(stdout, f"Colonne déjà présente : {table}.{column}")
        return False
    _log(stdout, f"Ajout colonne manquante : {table}.{column}")
    editor.add_field(model, field)
    return True


def _add_index_if_missing(editor, model, index_name: str, stdout=None):
    for index in model._meta.indexes:
        if index.name == index_name:
            if _index_exists(index.name):
                _log(stdout, f"Index déjà présent : {index.name}")
                return False
            _log(stdout, f"Ajout index manquant : {index.name}")
            editor.add_index(model, index)
            return True
    return False


def repair_pfmp_rc16_schema(mark_migration: bool = True, stdout=None):
    """Rend le schéma PFMP RC16 cohérent et idempotent.

    La fonction peut être appelée :
    - par une commande Django avant/après migrate ;
    - par la migration 0002 elle-même.
    """
    from pfmp_manager.models import (
        PfmpUser, Company, CompanyContact, CompanyTag, ImportBatch,
        StudentCompanySearch, StudentCompanyAction,
    )

    with connection.schema_editor() as editor:
        # Tables nouvelles indépendantes ou quasi indépendantes.
        _create_model_if_missing(editor, CompanyTag, stdout)
        _create_model_if_missing(editor, ImportBatch, stdout)

        # Champs ajoutés à PfmpUser.
        for field_name in ['address', 'postal_code', 'city', 'latitude', 'longitude']:
            _add_field_if_missing(editor, PfmpUser, field_name, stdout)

        # Champs ajoutés à Company.
        for field_name in [
            'external_key', 'siret', 'naf_ape', 'source_activity', 'domains_text',
            'subdomains_text', 'country', 'full_address', 'geocoding_status',
            'osm_search_url', 'student_visible', 'import_source', 'import_batch',
        ]:
            _add_field_if_missing(editor, Company, field_name, stdout)

        # Table M2M Company.tags.
        try:
            through = Company.tags.through
            _create_model_if_missing(editor, through, stdout)
        except Exception as exc:  # Défensif : ne bloque pas la réparation globale.
            _log(stdout, f"Avertissement M2M tags : {exc}")

        # Index Company.
        for index_name in ['pfmp_manage_name_4567_idx', 'pfmp_manage_city_93d0_idx', 'pfmp_manage_postal_c1d1_idx']:
            _add_index_if_missing(editor, Company, index_name, stdout)

        # Champs ajoutés à CompanyContact.
        for field_name in [
            'mobile_phone', 'student_visible', 'teacher_visible', 'personal_address',
            'personal_postal_code', 'personal_city', 'personal_latitude',
            'personal_longitude', 'use_personal_location_for_student_search',
            'can_help_transport', 'import_source', 'import_batch',
        ]:
            _add_field_if_missing(editor, CompanyContact, field_name, stdout)

        for index_name in ['pfmp_manage_email_71f0_idx', 'pfmp_manage_contact_1b3e_idx']:
            _add_index_if_missing(editor, CompanyContact, index_name, stdout)

        # Tables de recherche élève.
        _create_model_if_missing(editor, StudentCompanySearch, stdout)
        for index_name in ['pfmp_manage_student_24f1_idx', 'pfmp_manage_status_34e3_idx']:
            _add_index_if_missing(editor, StudentCompanySearch, index_name, stdout)

        _create_model_if_missing(editor, StudentCompanyAction, stdout)

    if mark_migration:
        _mark_migration('pfmp_manager', '0002_rc16_pfmp_complete')
        _log(stdout, "Migration pfmp_manager.0002_rc16_pfmp_complete marquée comme appliquée si nécessaire.")
