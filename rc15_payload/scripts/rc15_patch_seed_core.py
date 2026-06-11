#!/usr/bin/env python3
"""Patch idempotent de seed_core.py pour éviter les doublons username/code en démo."""
from pathlib import Path
import re

path = Path("lp-core-app/core/management/commands/seed_core.py")
if not path.exists():
    print("seed_core.py introuvable, patch ignoré")
    raise SystemExit(0)

text = path.read_text(encoding="utf-8")
new_func = '''    def _upsert_user(self, *, code, username, password, first_name, last_name, formation, class_name, role, rights):
        CoreClass.objects.get_or_create(formation=formation, name=class_name, school_year='2025-2026')

        # RC15 : idempotence forte. Les imports XLSX peuvent créer un utilisateur
        # avec username=PROF-0001 mais code différent. On cherche donc d'abord
        # par code, puis par username, avant toute création afin d'éviter
        # l'erreur UNIQUE sur core_coreuser.username.
        user = CoreUser.objects.filter(code=code).order_by('id').first()
        if user is None:
            user = CoreUser.objects.filter(username=username).order_by('id').first()
        created = user is None
        if user is None:
            user = CoreUser(code=code, username=username)

        changed = created
        for field, value in {
            'code': code,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'formation': formation,
            'class_name': class_name,
            'role_principal': role,
            'rights': rights,
            'active': True,
            'school_year': '2025-2026',
            'initial_password_for_sync': password,
            'source': 'demo',
        }.items():
            if hasattr(user, field) and getattr(user, field) != value:
                setattr(user, field, value)
                changed = True
        if created or not getattr(user, 'password_hash', ''):
            user.set_password(password)
            changed = True
        if changed:
            user.save()
        return user
'''

pattern = r"    def _upsert_user\(self, \*, code, username, password, first_name, last_name, formation, class_name, role, rights\):\n.*?\n    def handle\(self, \*args, \*\*options\):"
replacement = new_func + "\n    def handle(self, *args, **options):"
new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
if count == 0:
    print("Fonction _upsert_user non trouvée ou déjà modifiée, patch ignoré")
    raise SystemExit(0)
path.write_text(new_text, encoding="utf-8")
print("seed_core.py patché pour idempotence RC15")
