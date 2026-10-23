# NATHAN — prototype matériel Pi 3 A+ par Codex

**Checkpoint de conception, sans autorisation de fabrication.** Auteur : Codex/OpenAI, agent `nathan_bom` et intégration par l'agent parent, 22 octobre 2026. Ce lot répond à la demande de deux PCB, d'un boîtier reconstruit à partir de l'apparence historique et d'un assemblage CAO incluant les cartes. Le routage et l'assemblage complet restent à produire dans une mise à jour de la PR.

La proposition d'architecture est [ADR-0008 — Proposé](../../docs/decisions/0008-prototype-pi3a-deux-pcb-pisugar.md). Elle conserve les écarts visibles avec les exigences et ADR acceptés : Pi 3 A+, port micro-USB demandé malgré USB-C dans R-24, contrat USB CDC à préserver et ADC 12 bits. Aucun jalon n'est déclaré terminé.

## État exact du checkpoint

| Livrable | Révision et état |
|---|---|
| [Carte commandes](pcb/controls/nathan-controls.kicad_pcb) | D0.1, 31 empreintes de placement ; aucune piste ni zone. Deux groupes cardinaux de quatre boutons, deux centraux, sticks proposés en dessous, réserves L1/L2 et R1/R2. |
| [Carte porteuse](pcb/base/nathan-base.kicad_pcb) | D0.1, 6 empreintes et réserves Pi/PiSugar/audio ; aucune piste ni zone. |
| [Schémas commandes](electrical/controls/nathan-controls.kicad_pro) | D1, 93 composants physiques proposés et 4 déclarations ERC. Netlist native exportée et ERC à zéro erreur/avertissement avec le lancement décrit ci-dessous. |
| [Schémas porteuse](electrical/base/nathan-base.kicad_pro) | D1, huit interfaces ; circuits USB/audio encore incomplets. |
| [Coque paramétrique](mechanical/nathan-enclosure.scad) | Source OpenSCAD texte, non compilée ; ouvertures et fixations fonctionnelles encore à qualifier. Aucun assemblage FreeCAD livré dans ce checkpoint. |

Les PCB D0.1 et les schémas D1 sont **deux étapes différentes**. Le contrat intercartes D1 affecte les broches 15/16 à `3V3_PI` et `CTRL_RESET_N`, auparavant réservées : ne pas mélanger les révisions. Détails, composants candidats et sources fabricant : [electrical/README.md](electrical/README.md), [pin-map.csv](electrical/pin-map.csv) et [bom-proposal.csv](electrical/bom-proposal.csv).

L'empilement proposé utilise une porteuse de support et une nappe GPIO polarisée : le PiSugar occupe le dessous du Pi avec ses contacts pogo, tandis que le GPIO du Pi est orienté vers le haut. Les connecteurs/réserves D0 ne prouvent pas l'accouplement de pièces réelles. PiSugar 3 Plus reste un candidat à qualifier sur le bilan de puissance et le kit réel.

## Vérifications et limites

| Contrôle effectué | Résultat |
|---|---|
| Lecture numérique des anciens STL | Trois fichiers mesurés et hachés ; profil simplifié à 38 points. Millimètres supposés, car STL n'impose pas d'unité. |
| Contrôle textuel D0.1 | S-expressions équilibrées, coordonnées finies, absence d'empreinte vide et de référence dupliquée ; courtyards rectangulaires avant sans chevauchement au test. Réserves et volumes 3D non couverts. |
| Chargement et DRC natifs de commandes D0.1 | Chargement réussi ; 0 violation géométrique et **5 connexions non routées** sur J_LINK. Cela ne valide pas les circuits D1. |
| Schéma commandes D1 | Export natif et comparaison initiale broche par broche sans écart ; ERC courant : **0 erreur, 0 avertissement**. |
| Reproductibilité ERC KiCad 8.0.2 | Deux profils neufs non initialisés ont provoqué une sortie `0xC0000005`. Deux profils neufs préinitialisés avec la table d'empreintes officielle ont réussi. Le runner applique ce contournement ; la cause interne reste inconnue. |
| Essais matériels et CAO | Aucun essai électrique, thermique, USB, charge, autonomie, ergonomie ou contrôle complet des collisions de l'assemblage n'est revendiqué. |

Lire [l'incident KiCad](docs/incident-kicad.md). Les résultats courants sont dans `validation/native-current/` ; son sous-dossier `history/` et les anciens rapports à la racine de `validation/` sont des pièces de diagnostic. Un ERC réussi n'établit ni le dimensionnement du circuit, ni la conformité des empreintes fabricant.

## Reproduire les contrôles

Outils employés : KiCad **8.0.2** et son Python, Python 3.12 pour le lanceur. FreeCAD **1.1.4** portable a été autorisé et vérifié séparément pour la suite de la CAO ; son exécutable et ses archives ne sont pas distribués dans cette PR. SOLIDWORKS n'est pas utilisé.

Depuis ce dossier, avec KiCad 8 installé et `python` disponible :

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
# Facultatif si KiCad 8 est installé ailleurs :
# $env:KICAD_BIN = 'C:\Program Files\KiCad\8.0\bin'
python tools/preflight_text.py
python tools/run_native_check.py netlist controls
python tools/compare_native_netlist.py controls
python tools/run_native_check.py erc controls
```

Le runner borne chaque opération native à 20 secondes, journalise son PID et ne termine que son propre processus en cas de dépassement. Il initialise son profil **local au dossier de conception** avec le `fp-lib-table` de la distribution KiCad, sans copier le profil personnel. Les anciens rapports sont archivés et la création du nouveau rapport est vérifiée. Un autre profil peut être choisi avec `--config-dir validation/native-current/config/mon-essai` ; il doit rester dans ce dossier de conception.

Ici, `load` et `drc` ciblent les cartes **D0.1 dans `pcb/`**, tandis que `netlist` et `erc` ciblent les schémas **D1 dans `electrical/`**. Les anciens scripts `build_design.py` et `validate_design.py` conservent leur garde après l'incident historique.

## Suite et points de revue

1. Terminer les circuits USB/audio et le choix des pièces physiques, notamment commandes, connecteurs, câbles et alimentation.
2. Reporter la netlist finale dans les deux PCB, placer et router ; vérifier DRC, connexions restantes et correspondance aux schémas.
3. Construire l'assemblage FreeCAD éditable avec cartes, pièces réelles ou enveloppes explicitement identifiées, boîtier et mécanismes ; vérifier jeux et débattements.
4. Qualifier sur matériel le montage Pi/PiSugar, les courants, la charge, l'USB, l'audio et les moteurs avant toute fabrication finale.

Paramètres et origine : [design.json](parameters/design.json), [contexte et écarts](docs/contexte-et-ecarts.md), [disposition des commandes](docs/disposition-commandes.md). Les huit boutons de face et le style des épaules sont demandés ; coordonnées précises, sticks symétriques et dimensions sont des propositions. Largeur nominale 160 mm et hauteur allouée 66 mm, sans validation ergonomique.

Le dépôt historique et le classeur BOM original n'ont pas été modifiés. Les formes du boîtier sont reconstruites ; les solides historiques ne sont pas réimportés comme pièces nouvelles. Aucun achat, activation de licence ou lancement de fabrication n'est effectué.
