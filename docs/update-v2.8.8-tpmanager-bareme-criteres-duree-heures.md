# LP Gestion Atelier Suite v2.8.8 — TP Manager barème critères et durée en heures

Type : mise à jour SSH / compatible `upgrade_module.sh tpmanager`.

## Modifications

- La durée des TP se saisit maintenant en heures dans le formulaire (`Durée (h)`).
- La base conserve le stockage historique en minutes pour compatibilité.
- La page `Affecter / barème` conserve uniquement le statut pédagogique sur les compétences.
- Les pourcentages et points sont portés uniquement par les critères / sous-compétences officiels.
- Les points des critères sont calculés automatiquement à partir du total du TP : `points = total × pourcentage / 100`.
- Migration `0008_tpv2_bareme_on_criteria_only` : nettoyage des anciens points/pourcentages éventuellement placés sur les compétences.

## Installation

```bash
./upgrade_module.sh tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.8.8-tpmanager-bareme-criteres-duree-heures.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py check
```
