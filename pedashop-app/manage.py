#!/usr/bin/env python
"""Point d’entrée Django de PedaShop.

Ce fichier reste volontairement standard pour faciliter les maintenances :
- `python manage.py migrate` applique les migrations ;
- `python manage.py seed_pedashop` crée les données de base ;
- `python manage.py sync_lp_core_users` synchronise les utilisateurs LP Core.
"""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pedashop_project.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
