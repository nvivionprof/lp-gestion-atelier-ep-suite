# ToolMag V27 — inventaires et statut absent

Corrections apportées :

- Renommage des colonnes de la fiche matériel :
  - `Obligatoire` devient `Présent` ;
  - `État attendu` devient `Statut`.
- Ajout du choix `Absent` dans les statuts de composants lors des inventaires.
- Normalisation de la saisie :
  - si le statut d'un composant est `Absent`, la présence est automatiquement considérée comme non cochée ;
  - si la présence n'est pas cochée, le statut enregistré devient `Absent`.
- Inventaire utilisateur : les cases restent vides par défaut.
- Inventaire magasinier : le préremplissage reste basé sur l'inventaire utilisateur soumis ou le dernier contrôle magasinier connu.
