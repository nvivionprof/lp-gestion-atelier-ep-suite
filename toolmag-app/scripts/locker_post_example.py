#!/usr/bin/env python3
"""Exemple de script serveur d’ouverture casier.
ToolMag envoie un JSON sur stdin. Remplacer la partie print par l'appel POST réel vers Node-RED/ESP32.
Aucune URL de contrôleur n'est stockée dans les fiches matériel.
"""
import json
import sys
from datetime import datetime

payload = json.load(sys.stdin)
# Exemple : ici on ne fait qu'écrire dans la sortie standard pour test.
print(json.dumps({
    "ok": True,
    "message": "Simulation ouverture casier",
    "received": payload,
    "processed_at": datetime.now().isoformat(),
}, ensure_ascii=False))
