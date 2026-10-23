# Journal des décisions (ADR)

> **Architecture Decision Records** — un fichier par décision d'architecture ou de conception.
> C'est la **frise chronologique** du *pourquoi* du projet : un nouvel arrivant lit ce journal pour comprendre comment NATHAN en est arrivé là, et comment les choix ont évolué.

## Comment ça marche

- **Un ADR = une décision**, dans un fichier `NNNN-titre.md` numéroté et daté.
- Un ADR **accepté est immuable**. Si une décision change, on **n'édite pas** l'ancien : on crée un nouvel ADR avec le statut *« Remplace ADR-XXXX »*, et l'ancien passe à *« Remplacé par ADR-YYYY »*. L'historique des virages reste lisible.
- Chaque ADR **lie** les besoins/requis/contraintes/hypothèses (`R-`, `C-`, `H-`, `E-`) et les tâches (`TACHES.md`) concernés.
- Voir [`CONTRIBUTING.md`](../../CONTRIBUTING.md) pour le gabarit et la procédure.

**Légende des statuts :** `Proposé` · `Accepté` · `Remplacé par ADR-XXXX` · `Déprécié`

## Index

| # | Décision | Statut | Date | Bloc concerné |
|---|----------|--------|------|---------------|
| [0001](./0001-architecture-pc-first-interfaces.md) | Architecture PC-first et contrats d'interface | ✅ Accepté | 2026-05-15 | Tous (fondation) |
| [0002](./0002-librairie-son-spatial-maison.md) | Librairie de son spatial **maison** (HRTF) | ✅ Accepté | 2026-06-07 | Audio |
| [0003](./0003-choix-mcu-benchmark-driven.md) | Choix du MCU **piloté par benchmark** (3 gammes) | ✅ Accepté | 2026-06-07 | PCB / Audio |
| [0004](./0004-option-repli-audio-fpga.md) | Option de repli audio **matérielle (FPGA/CPLD)** | ✅ Accepté *(activation conditionnelle)* | 2026-06-07 | Audio / PCB |
| [0005](./0005-micropython-mini-jeux-usb-cdc.md) | **MicroPython** pour les mini-jeux + USB CDC | ✅ Accepté | fondatrice | Game Engine / IDE |
| [0006](./0006-ide-accessible-assistance-vocale.md) | IDE accessible à **assistance vocale (TTS/STT + IA)** | ✅ Accepté *(orientation)* | 2026-06-07 | IDE |
| [0007](./0007-adoption-adr-structure-docs.md) | Adopter les **ADR** et la structure `docs/` | ✅ Accepté | 2026-06-07 | Gouvernance |
| [0008](./0008-prototype-pi3a-deux-pcb-pisugar.md) | Prototype Pi 3 A+, deux PCB et alimentation PiSugar | Proposé | 2026-10-22 | PCB / mécanique / alimentation |

## Décisions à venir (futurs ADR)

Chaque tâche **« DÉCISION »** de `TACHES.md` produira un ADR au moment où elle est tranchée :

| Tâche | Décision attendue | Quand |
|-------|-------------------|-------|
| `S7-T06` | **MCU effectivement retenu** (gamme A/B/C) | ~S7 sem 5 (fév. 2027) |
| `S7-T07` | **Chemin audio** : software pur / DSP externe / **FPGA-CPLD** (active ou non ADR-0004) | ~S7 sem 5 |
| `TECH-19` | **Stack de l'IDE** (Electron/React, Tauri, …) | S7 sem 1-2 |
