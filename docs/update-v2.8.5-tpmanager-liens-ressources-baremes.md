# Mise à jour v2.8.5 — TP Manager : liens TP, ressources en blocs OU et barèmes

## Type
Installation complète ou mise à jour SSH. Compatible avec la mise à jour par module introduite en v2.8.3.

## Principes ajoutés

- Ajout d’une arborescence de TP liés : blocs de TP avant/prérequis et blocs de TP après/poursuite.
- Chaque TP lié peut être marqué **conseillé** ou **obligatoire**.
- Refonte de la logique ressources : chaque bloc est un **bloc OU** ; plusieurs blocs successifs sont interprétés en **ET** entre eux.
- Ajout d’une recherche de ressources par origine : ToolMag, System Manager, PedaShop ou saisie manuelle.
- Ajout du type de mobilisation des compétences et critères officiels : mobilisé, travaillé, évalué, certification.
- Ajout de barèmes sur compétences officielles et critères officiels pour préparer une notation automatique.
- Ajout d’une bibliothèque de critères de réussite et d’évaluation finale, filtrable par diplôme, métier, thème et usage, avec ajout manuel toujours possible.

## Protection

- Les bases ToolMag, PedaShop et System Manager sont montées en lecture seule dans TP Manager.
- TP Manager référence les ressources externes mais ne modifie jamais les bases des autres modules.
- Migration additive 0005, non destructive.
