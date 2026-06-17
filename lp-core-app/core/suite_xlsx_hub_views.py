from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def suite_xlsx_hub(request):
    modules = [
        {"name": "LP Core", "url": "/xlsx/", "description": "Utilisateurs, droits, formations, paramètres communs."},
        {"name": "ToolMag", "url": "/toolmag/xlsx/", "description": "Matériels, catégories, emplacements, composants, prêts."},
        {"name": "Safety Manager", "url": "/safety/xlsx/", "description": "DUERP, risques, événements, actions sécurité."},
        {"name": "PedaShop", "url": "/pedashop/xlsx/", "description": "Articles, stocks, bons, magasins, mouvements."},
        {"name": "System Manager", "url": "/system/xlsx/", "description": "Systèmes, zones, documents, maintenances, réservations."},
        {"name": "TP Manager", "url": "/tpmanager/xlsx/", "description": "TP, thèmes, compétences, systèmes associés."},
        {"name": "PFMP Manager", "url": "/pfmp/xlsx/", "description": "Entreprises, contacts, relais, périodes, recherches."},
    ]
    return render(request, "core/suite_xlsx_hub.html", {"modules": modules})
