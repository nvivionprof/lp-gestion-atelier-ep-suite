"""Petites aides de permissions.

Les vues utilisent ces fonctions pour conserver un contrôle simple et lisible :
- utilisateur : consultation et demandes ;
- professeur : réservations et demandes TP ;
- magasinier : préparation, distribution, transferts ;
- admin : paramétrage complet.
"""
from django.contrib import messages
from django.shortcuts import redirect
from .models import PedaShopUser


def current_user(request):
    uid = request.session.get('pedashop_user_id')
    if not uid:
        return None
    return PedaShopUser.objects.filter(id=uid, active=True).first()


def require_login(request):
    user = current_user(request)
    if not user:
        messages.error(request, 'Connexion PedaShop nécessaire.')
        return None
    return user


def require_storekeeper(request):
    user = require_login(request)
    if not user:
        return None
    if not user.is_storekeeper_like:
        messages.error(request, 'Accès réservé au magasinier, professeur ou administrateur.')
        return None
    return user


def require_admin(request):
    user = require_login(request)
    if not user:
        return None
    if not user.is_admin_like:
        messages.error(request, 'Accès réservé à l’administrateur PedaShop.')
        return None
    return user
