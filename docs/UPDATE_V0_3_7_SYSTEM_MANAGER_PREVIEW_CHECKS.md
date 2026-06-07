# V0.3.7 — System Manager : prévisualisation Office, checks, anomalies, droits temporaires

## Ajouts principaux

- Conversion automatique DOCX/XLSX/PPTX/ODT/ODS/ODP en PDF via LibreOffice headless.
- Conservation du fichier original et bouton téléchargement original + PDF.
- Bouton Ajouter directement dans chaque conteneur documentaire.
- Conteneur virtuel `00 - Checks par défaut` dans le classeur du système.
- Réponses attendues Oui / Non / NC sur les checks.
- Création automatique d'anomalies si la réponse diffère de la réponse attendue.
- Levée d'anomalie : directe si non bloquante, validation professeur/admin si bloquante.
- Droits temporaires accordables à un utilisateur ou à une classe.
- Prise de poste simplifiée : suppression des champs formation/niveau/classe/groupe, contexte repris depuis la réservation.
- Affichage dynamique `/system/affichage/` : systèmes utilisés par zone et anomalies en rouge.

## Installation

```bash
cd /home/user/docker/lp-gestion-atelier-ep-suite
rm -rf /home/patch-v0.3.7-system-manager
unzip /home/lp-gestion-atelier-ep-suite-patch-v0.3.7-system-manager-preview-checks.zip -d /home/patch-v0.3.7-system-manager
chmod +x /home/patch-v0.3.7-system-manager/scripts/apply_update_v0.3.7_system_manager_preview_checks.sh
/home/patch-v0.3.7-system-manager/scripts/apply_update_v0.3.7_system_manager_preview_checks.sh /home/user/docker/lp-gestion-atelier-ep-suite
```

## Notes

La conversion Office nécessite le rebuild du conteneur System Manager car LibreOffice est installé dans l'image.
