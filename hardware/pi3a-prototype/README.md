# NATHAN — prototype Pi 3 A+ à deux PCB

**En pause à la demande d’Arthur pour limiter la consommation.** Checkpoint D1-3, Codex/OpenAI (`nathan_bom` et parent), 22 octobre 2026. Proposition de conception, sans autorisation de fabrication ni jalon déclaré terminé.

## Voir le travail

- [Vue assemblée](mechanical/previews/nathan-review-assembled.png) et [vue éclatée](mechanical/previews/nathan-review-exploded.png).
- [Assemblage FreeCAD](mechanical/assembly/nathan-D1-review.FCStd) et [STEP](mechanical/assembly/nathan-D1-review.step).
- [Commandes KiCad](electrical/controls/nathan-controls.kicad_pro) et [porteuse KiCad](electrical/base/nathan-base.kicad_pro).
- [ADR-0008 proposé](../../docs/decisions/0008-prototype-pi3a-deux-pcb-pisugar.md), [revue USB-C](docs/usb-c-review.md), [reprise Claude](docs/reprise-claude.md).

Les images montrent la géométrie FreeCAD livrée. Largeur nominale 160 mm, hauteur de coque proposée 72 mm : **ébauche épaisse, ergonomie non validée**. Pi, PiSugar, batterie et certains mécanismes sont simplifiés ou représentés par des volumes réservés.

## État exact publié D1-3

| Livrable | État du checkpoint |
|---|---|
| Commandes | 93 composants + 4 fixations, quatre couches, pistes réelles. DRC : **0 erreur, 0 liaison ouverte, 17 avertissements** (7 vias pendants et 10 sérigraphies/bords). |
| Porteuse | 88 composants + 4 fixations, schéma GPIO/audio/USB-C et placement connecté. **257 liaisons ouvertes**, 4 erreurs de dégagement J120, 0 avertissement. Routage non terminé. |
| Schémas | ERC natif observé à zéro message sur les deux cartes. Les preuves et leurs périmètres figurent dans les rapports ; un ERC ne qualifie pas un circuit. |
| PCB/modèle | 337 pastilles numérotées commandes, 371 porteuse : zéro écart de net. Doublons physiques documentés. |
| Assemblage | STEP des deux cartes synchronisés, 58 formes valides. Huit paires ciblées sans intersection exacte, dont PCB/coques et commandes/L2. **Intersection des deux coques : 3,712 mm³**, à corriger. |

Le [manifeste D1-3](validation/checkpoint-d1-3.json) identifie les cartes, STEP, FCStd et rapports par SHA-256. [Revue mécanique indépendante](validation/parent/assembly-review-3.json). FCStd livré : `1a8ec46981c5897a12d664be2637b82b00acf471602682b01969a5fc0f7a3f11`.

`pcb/`, les sources OpenSCAD et `parameters/design.json` sont D0.1. Les projets D1 se trouvent dans `electrical/`, leur empilement dans `parameters/assembly-d1.json`. Ne pas mélanger les révisions de connectique.

## À reprendre

USB-C remplace la mention initiale micro-B selon la dernière précision d’Arthur. VBUS rejoint l’entrée du PiSugar, sa sortie alimente le Pi. Charge et utilisation simultanées dépendent du budget disponible. Batterie vide sur PC standard, logiciel d’autorisation de charge, transitions de courant, protection de la limite PiSugar 5,2 V et intégrité USB restent à résoudre ou qualifier.

La puissance des commandes doit être revue : tronc 5 V de 0,2 mm et boucle de convertisseur à améliorer. Les essais locaux de déplacement/découplage sont incomplets et **ne sont pas intégrés** à ce checkpoint. Le routage de la porteuse reste à faire.

Finaliser jonction de coque, ouvertures USB-C/casque, capteurs, ressorts, butées, câbles et dimensions du kit réel. Aucun essai matériel, thermique, autonomie, audio, haptique, USB ou ergonomie n’a été réalisé. Aucun export de production n’est fourni.

## Reproduction et précautions de reprise

KiCad 8.0.2 et FreeCAD 1.1.4 portable ont été utilisés. Aucun exécutable n’est distribué. Les générateurs `build_connected_*.py` écrasent les PCB : travailler dans une copie. Les scripts de routage sont les étapes historiques, pas une reconstruction complète qualifiée.

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
python tools/run_native_check.py erc controls
python tools/run_native_check.py erc base
```

Les contrôles natifs sont bornés et utilisent un profil local préparé depuis la distribution KiCad. Voir [l’incident KiCad](docs/incident-kicad.md). Les rapports intermédiaires restent diagnostiques : le manifeste indique ceux du checkpoint. Le dépôt historique et le classeur BOM original ne sont pas modifiés.
