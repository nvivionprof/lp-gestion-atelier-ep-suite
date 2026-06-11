# RC10 — Exports PDF d’activité élèves

Architecture retenue : chaque application possède une page `Configuration exports PDF` dans le menu admin.

Modes d’identité prévus :
- anonyme : Élève 001 ;
- nom seul ;
- prénom seul ;
- nom + prénom.

Filtres obligatoires : période début / fin.

Filtres métier par application :
- PedaShop : classe, groupe, magasin, type de bon, statut, article, réclamation ;
- System Manager : classe, groupe, système, zone, sous-zone, réservation, prise de poste, anomalie ;
- TP Manager : élève, classe, groupe, professeur, TP, thème, système, compétence, séquence ;
- ToolMag, Safety, PFMP : structure à raccorder aux modèles de chaque module.

Droits LP Core recommandés :
- LP_EXPORT_FICHES_ELEVES ;
- PEDASHOP_EXPORT_ACTIVITE ;
- SYSTEM_EXPORT_ACTIVITE ;
- TPMANAGER_EXPORT_ACTIVITE ;
- TOOLMAG_EXPORT_ACTIVITE ;
- SAFETY_EXPORT_ACTIVITE ;
- PFMP_EXPORT_ACTIVITE.
