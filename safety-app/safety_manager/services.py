from __future__ import annotations
from datetime import date


def current_year() -> int:
    return date.today().year


def priority_from_matrix(severity: int, frequency: int) -> tuple[int, str, int]:
    """Return priority, label and numeric score from DUERP severity/frequency matrix.

    Severity and frequency are intentionally limited to 1..4, consistent with the
    provided safety specification. The matrix is conservative for school workshops.
    """
    try:
        s = max(1, min(4, int(severity or 1)))
        f = max(1, min(4, int(frequency or 1)))
    except Exception:
        s, f = 1, 1
    score = s * f
    if score >= 9 or s == 4 or (s == 3 and f >= 3):
        return 1, 'Priorité 1 — critique à traiter en priorité', score
    if score >= 4:
        return 2, 'Priorité 2 — significatif à planifier', score
    return 3, 'Priorité 3 — maîtrisé/faible à surveiller', score


def next_code(model, prefix: str, date_field: str = 'created_at') -> str:
    """Generate PREFIX-YYYY-0001 style code without destructive assumptions."""
    year = current_year()
    start = f'{prefix}-{year}-'
    last = model.objects.filter(code__startswith=start).order_by('-code').first()
    if not last:
        return f'{start}0001'
    try:
        n = int(str(last.code).split('-')[-1]) + 1
    except Exception:
        n = model.objects.filter(code__startswith=start).count() + 1
    return f'{start}{n:04d}'


def user_is_safety_admin(user) -> bool:
    if not user:
        return False
    role = getattr(user, 'role_principal', '')
    rights = []
    if hasattr(user, 'rights_list'):
        rights = user.rights_list()
    return role in {'admin', 'admin_suite', 'responsable', 'responsable_securite'} or 'SAFETY_ADMIN' in rights or 'CORE_ADMIN' in rights


def user_can_edit_safety(user) -> bool:
    if not user:
        return False
    role = getattr(user, 'role_principal', '')
    rights = []
    if hasattr(user, 'rights_list'):
        rights = user.rights_list()
    return role in {'admin', 'admin_suite', 'responsable', 'responsable_securite', 'professeur', 'magasinier'} or 'SAFETY_EDIT' in rights or 'SAFETY_ADMIN' in rights


def user_can_declare_event(user) -> bool:
    if not user:
        return False
    role = getattr(user, 'role_principal', '')
    return role in {'admin', 'responsable', 'professeur', 'magasinier', 'utilisateur', 'eleve'} or user_can_edit_safety(user)
