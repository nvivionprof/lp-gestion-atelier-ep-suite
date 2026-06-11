#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
ADMIN_USER="$(env_get LP_CORE_ADMIN_USERNAME)"
ADMIN_PASS="$(env_get LP_CORE_ADMIN_PASSWORD)"
DJANGO_USER="$(env_get DJANGO_SUPERUSER_USERNAME)"
DJANGO_PASS="$(env_get DJANGO_SUPERUSER_PASSWORD)"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin}"
DJANGO_USER="${DJANGO_USER:-$ADMIN_USER}"
DJANGO_PASS="${DJANGO_PASS:-$ADMIN_PASS}"

log "Création/maj compte LP Core natif : $ADMIN_USER"
dc exec -T lp-core-app env LP_ADMIN_USER="$ADMIN_USER" LP_ADMIN_PASS="$ADMIN_PASS" python manage.py shell <<'PY'
import os
from django.contrib.auth.hashers import make_password
from core.models import CoreUser

username = os.environ.get("LP_ADMIN_USER", "admin")
password = os.environ.get("LP_ADMIN_PASS", "admin")
fields = {f.name for f in CoreUser._meta.fields}
lookup_field = "username" if "username" in fields else "code"
obj, _ = CoreUser.objects.get_or_create(**{lookup_field: username})

def set_if(name, value):
    if name in fields:
        setattr(obj, name, value)

set_if("username", username)
set_if("code", username)
set_if("first_name", "Admin")
set_if("last_name", "LP Core")
set_if("email", "")
set_if("role_principal", "admin")
set_if("rights", "CORE_ADMIN")
set_if("active", True)
set_if("is_active", True)
set_if("is_staff", True)
set_if("is_superuser", True)
set_if("source", "install")
set_if("force_password_change", True)
set_if("initial_password_for_sync", password)
if hasattr(obj, "set_password"):
    obj.set_password(password)
elif "password" in fields:
    obj.password = make_password(password)
obj.save()
print(f"Compte LP Core natif prêt : {username}")
PY

for svc in "${LP_MODULE_SERVICES[@]}"; do
  log "Création/maj admin Django : $svc"
  dc exec -T "$svc" env DJANGO_ADMIN_USER="$DJANGO_USER" DJANGO_ADMIN_PASS="$DJANGO_PASS" python manage.py shell <<'PY' || warn "Admin Django non créé pour ce module"
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get("DJANGO_ADMIN_USER", "admin")
password = os.environ.get("DJANGO_ADMIN_PASS", "admin")
u, _ = User.objects.get_or_create(username=username)
u.is_staff = True
u.is_superuser = True
u.is_active = True
if hasattr(u, "email"):
    u.email = getattr(u, "email", "") or ""
u.set_password(password)
u.save()
print(f"Compte Django prêt : {username}")
PY
 done
