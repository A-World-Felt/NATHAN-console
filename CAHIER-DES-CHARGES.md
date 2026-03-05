# Cahier des Charges — Projet NATHAN Console (v2.0)

**Projet :** NATHAN — Narrative Audio Terminal for Humans with Alternative Navigation
**Version du document :** 2.0
**Date :** 2026-03-05
**Auteur :** Arthur Olivier Fortin
**Statut :** Phase de conception majeure

---

## Table des matières

1. [Contexte et vision du projet](#1-contexte-et-vision-du-projet)
2. [État actuel du projet (v1.0)](#2-état-actuel-du-projet-v10) — *inclut jeu existant GlassBreaker et IDE Cantante*
3. [Objectifs du projet majeur (v2.0)](#3-objectifs-du-projet-majeur-v20)
4. [Public cible](#4-public-cible)
5. [Équipes, rôles et stratégie de développement parallèle](#5-équipes-rôles-et-stratégie-de-développement-parallèle)
6. [Spécifications hardware (v2.0)](#6-spécifications-hardware-v20)
7. [Spécifications firmware et logiciel bas niveau](#7-spécifications-firmware-et-logiciel-bas-niveau)
8. [Spécifications du game engine](#8-spécifications-du-game-engine)
9. [Spécifications du premier jeu — La Maison de Nathan](#9-spécifications-du-premier-jeu--la-maison-de-nathan)
10. [Système de mini-jeux](#10-système-de-mini-jeux)
11. [Contraintes et risques techniques](#11-contraintes-et-risques-techniques)
12. [Planification par workstreams et dépendances](#12-planification-par-workstreams-et-dépendances)
13. [Budget](#13-budget)
14. [Livrables](#14-livrables)

---

## 1. Contexte et vision du projet

### 1.1 Origine

Le projet NATHAN est né en 2022 de la collaboration entre Arthur Olivier Fortin et Nathan Therrien, musicien aveugle et passionné de synthétiseurs. L'objectif initial était de concevoir une console de jeu entièrement accessible aux personnes non-voyantes, dans laquelle le son et les sensations tactiles remplacent intégralement l'image.

### 1.2 Mission

Créer une console de jeu **open-source**, **abordable** et **inclusive**, où l'expérience est entièrement auditive et haptique. La console doit permettre à un utilisateur non-voyant de jouer les yeux fermés, avec une immersion complète par le son spatial 3D et le retour vibratoire directionnel.

### 1.3 Vision long terme

- Être la première console de jeu grand public dédiée aux personnes ayant une déficience visuelle.
- Permettre aux utilisateurs de **créer leurs propres mini-jeux** sans barrière technique (MicroPython).
- Constituer une **plateforme pédagogique** : initiation à la programmation pour les personnes non-voyantes.
- Rester open-source pour favoriser la contribution communautaire.

---

## 2. État actuel du projet (v1.0)

### 2.1 Ce qui est complété

| Composant | État | Détails |
|-----------|------|---------|
| Modèles 3D boîtier | ✅ Complet | 3 pièces SolidWorks (.SLDPRT), STL générés |
| PCB KiCAD | ✅ Complet | Gerbers prêts pour fabrication |
| BOM (liste de matériaux) | ✅ Documenté | Composants sourcés |
| Documentation README | ✅ Rédigé | Histoire, vision, fonctionnalités |

### 2.2 Matériel actuel (v1.0)

| Composant | Spécification |
|-----------|---------------|
| Microcontrôleur | Raspberry Pi Pico (RP2040) |
| Boutons | 5 (3 arcade 30mm + 2 micro switches) |
| LEDs | 5 (indicateurs visuels) |
| Moteurs haptiques | 2 (moteurs Xbox rumble) |
| Audio | Jack stéréo 3.5mm |
| Stockage | Module micro SD |
| Alimentation | 3x piles AA |
| Potentiomètre | WH148 1kΩ |

### 2.3 Ce qui n'existe pas encore (côté console v2.0)

- Firmware ESP32-S3 : **non démarré** (à écrire en C/C++ avec ESP-IDF)
- Game engine spatial : **non démarré**
- IDE mini-jeux (intégration NATHAN) : **en cours** (voir 2.5)

### 2.4 Jeu existant — GlassBreaker (CircuitPython, Raspberry Pi Pico)

Un jeu complet est déjà fonctionnel dans le dépôt `NATHAN-code`. Il tourne sur le **Raspberry Pi Pico** en **CircuitPython 8.x** et constitue la référence directe pour l'architecture des mini-jeux futurs.

**Dépôt :** `C:\Users\arthu\OneDrive\NATHAN\NATHAN-code` (GlassBreaker Safe CP)

#### Architecture du jeu existant

```
GlassBreaker Safe CP/
├── main.py              # Orchestre tous les managers
├── input/buttons.py     # ButtonManager — lecture GPIO
├── output/audio.py      # AudioManager — PWM 22050Hz mono
├── output/leds.py       # LEDManager — 7 LEDs
├── output/motors.py     # MotorManager — 2 moteurs rumble
├── game/logic.py        # GameLogic + GameState
├── game/menu.py         # MenuSystem + MenuExtension
├── utils/memory.py      # MemoryManager — scores SD card
├── sounds/              # Fichiers WAV sur carte SD
└── lib/                 # Bibliothèques Adafruit CircuitPython
```

#### Mécaniques de jeu

- **Type :** Jeu de réaction bouton (audio-first)
- **5 modes :** Arcade (sons), Voice (voix), Reverse, Light (visuel), Megamix (aléatoire)
- **Difficulté progressive :** `timeout = max(0.5, 1.0 - (0.001 × score))`
- **Jalons :** Annonces audio à 25, 50, 75, 100 points
- **Persistance :** High scores par mode sur carte SD (FAT32)

#### Ce que cela implique pour v2.0

| Aspect | GlassBreaker (v1) | NATHAN v2.0 |
|--------|-------------------|-------------|
| Langage jeu | CircuitPython | C/C++ (game engine) |
| Langage mini-jeux | CircuitPython | MicroPython (quasi-identique) |
| Audio | PWM mono 22050 Hz | I2S stéréo binaural HRTF |
| Entrées | 5 boutons | 2 joysticks + boutons |
| Haptique | 2 moteurs (on/off) | 5 moteurs arc (PWM intensité) |
| Pattern module | Manager + MenuExtension | HAL + API game engine |

> **Note de compatibilité :** CircuitPython et MicroPython partagent ~95% de leur syntaxe. Les mini-jeux écrits pour v2.0 s'inspireront directement des modules GlassBreaker. Le `MenuExtension` pattern existant (classe avec `run()` et métadonnées) devient le modèle du format mini-jeu MicroPython.

#### Pattern MenuExtension (référence pour le format mini-jeu)

```python
# Modèle inspiré de game/menu.py (GlassBreaker)
class MonMiniJeu:
    META = {
        "title": "Mon Mini-Jeu",
        "author": "Arthur",
        "description": "Description audio du jeu"
    }

    def __init__(self, managers):
        self.audio = managers["audio"]
        self.buttons = managers["buttons"]
        self.motors = managers["motors"]

    def run(self):
        """Boucle principale — retourne True si succès, False si échec"""
        pass
```

### 2.5 IDE existant — Cantante (Electron + React + TypeScript)

**Dépôt :** `C:\Cantante`

Cantante est l'application desktop qui servira d'IDE pour programmer les mini-jeux. Elle est en développement actif et sera intégrée dans ce repo sous `ide/`.

**Stack :** Electron 28 + React 18 + TypeScript 5.3 + Vite 5

#### Ce qui est déjà implémenté dans Cantante

| Fonctionnalité | État | Détail |
|----------------|------|--------|
| Éditeur de code multi-onglets | ✅ Complet | Textarea + coloration syntaxique custom |
| Explorateur de fichiers (sidebar) | ✅ Complet | Arborescence avec create/delete |
| Recherche & remplacement | ✅ Complet | Case-insensitive, replace-all |
| Terminal intégré | ✅ Complet | Exécution de commandes shell avec streaming |
| Accessibilité vocale (TTS) | ✅ Complet | Web Speech API, **français par défaut (fr-FR)** |
| Screen reader (ARIA live) | ✅ Complet | Annonces assistives |
| Raccourcis clavier | ✅ Complet | Ctrl+F, Ctrl+S, Ctrl+Shift+P, etc. |
| Palette de commandes | ✅ Complet | Ctrl+Shift+P |
| Maestro backend (IA, C# .NET) | ✅ Intégré | Sidecar HTTP, agent "Jarvis" (ask) |
| Coloration syntaxique TypeScript/JS | ✅ Complet | Tokenizer regex custom |

#### Ce qui manque dans Cantante pour NATHAN

| Fonctionnalité | Priorité | Notes |
|----------------|----------|-------|
| Coloration syntaxique MicroPython | Critique | Remplacer/compléter le tokenizer TS |
| Auto-complétion API `nathan.*` | Critique | Nécessite Monaco Editor ou extension |
| Communication USB série (console) | Critique | Web Serial API ou `serialport` npm |
| Upload de `.py` vers carte SD via USB | Critique | Dépend de la communication USB |
| Visualisateur de scène 2D (sons spatiaux) | Haute | Drag & drop, coordonnées x/y/z |
| Simulation audio WebAudio HRTF | Moyenne | Aperçu avant envoi sur console |
| Gestionnaire de mini-jeux (liste SD) | Haute | Lecture liste depuis console |
| Mode d'affichage accessible (grand texte, contraste) | Haute | Accessibilité DV |

> **Cantante est développé séparément.** Son cahier des charges est indépendant de ce document. L'intégration avec la console NATHAN se fera via le protocole USB CDC défini dans la section 7.4. Une fois ce protocole établi, Cantante sera intégré dans ce repo sous `ide/`.

---

## 3. Objectifs du projet majeur (v2.0)

Le projet v2.0 constitue une **refonte complète** articulée autour de quatre axes :

### Axe 1 — Refonte hardware
Remplacer le Raspberry Pi Pico par un **ESP32-S3**, ajouter **2 joysticks analogiques**, **5 moteurs de vibration en arc**, et migrer vers une **batterie LiPo USB-C rechargeable**.

### Axe 2 — Game engine embarqué
Développer un moteur de jeu en **C/C++** tournant entièrement sur l'ESP32-S3, avec un système de placement 2D+hauteur permettant le calcul automatique d'**audio spatial binaural (HRTF)**.

### Axe 3 — Premier jeu : La Maison de Nathan
Développer le jeu de démonstration de la console : un jeu entièrement auditif et haptique mettant en scène Nathan, un aveugle, dans sa maison.

### Axe 4 — Système de mini-jeux
Permettre aux utilisateurs de programmer et jouer à des mini-jeux écrits en **MicroPython** via l'IDE Cantante (développé séparément).

---

## 4. Public cible

### 4.1 Utilisateurs finaux (joueurs)

- **Primaire :** Personnes non-voyantes ou malvoyantes, tous âges
- **Secondaire :** Personnes voyantes souhaitant une expérience sensorielle immersive

### 4.2 Utilisateurs créateurs (programmeurs de mini-jeux)

- **Primaire :** Personnes non-voyantes apprenant la programmation
- **Secondaire :** Développeurs souhaitant créer du contenu pour la plateforme
- **Niveau requis :** Débutant (MicroPython simplifié, interface graphique)

### 4.3 Contraintes d'accessibilité prioritaires

- Toute interface de jeu doit fonctionner **sans retour visuel**
- Tous les menus et interactions doivent être **entièrement navigables au son**
- Le boîtier doit être **ergonomique** et les contrôles **facilement différenciables au toucher**

---

## 5. Équipes, rôles et stratégie de développement parallèle

### 5.1 Composition des équipes

| Équipe | Code | Profil | Responsabilité |
|--------|------|--------|----------------|
| **Électrique** | ELEC | Génie électrique | Schéma, PCB, boîtier, soudure, validation matérielle |
| **Engine** | ENG | Génie informatique | Game engine, scènes, collisions, bâton, MicroPython, HAL |
| **Audio spatial** | AUD | Génie informatique (spécialisé signal/audio) | Pipeline HRTF, mix binaural, évaluation software vs DSP |
| **Jeu / Contenu** | JEU | Génie informatique / design | Design des pièces, mécaniques de jeu, banque de sons, narration |

### 5.2 Principe fondamental : zéro temps d'attente entre équipes

Le plan de développement est conçu pour que **aucune équipe ne soit bloquée** par une autre. Cela repose sur trois stratégies :

#### Stratégie A — Manette de substitution (découple ELEC ↔ ENG/JEU)

Dès le **jour 1** du projet, les équipes logicielles utilisent une **manette USB grand public** (type DualShock 4 / Xbox One, ~30$ CAD) pour développer et tester toute la logique de jeu.

Un module **InputMapper** abstrait complètement le matériel :

```
┌───────────────────────────────────────────────┐
│                 Game Engine                     │
│                                                 │
│    scene.update(input, dt)                      │
│         │                                       │
│    ┌────▼─────┐                                 │
│    │InputMapper│  ← Interface abstraite          │
│    └────┬─────┘                                 │
│         │                                       │
│    ┌────┴──────────────┬──────────────────┐     │
│    │                   │                  │     │
│  GamepadMapper    NathanMapper       DebugMapper│
│  (DualShock/Xbox) (manette réelle)   (clavier)  │
│  PHASE 1-2        PHASE 3+           DEBUG      │
└───────────────────────────────────────────────┘
```

| Implémentation | Utilisée par | Phase | Description |
|----------------|-------------|-------|-------------|
| `GamepadMapper` | ENG, JEU, AUD | Phases 1-2 | Manette USB standard. Joystick L/R mappés directement, vibration mono simulée. |
| `DebugMapper` | ENG | Toutes | Clavier + souris pour tests rapides sans manette |
| `NathanMapper` | ENG, ELEC | Phase 3+ | Manette NATHAN réelle. Joysticks ADC, 5 moteurs PWM, boutons GPIO. |

**Mapping de substitution (GamepadMapper):**

| Contrôle NATHAN | Substitut DualShock/Xbox |
|-----------------|--------------------------|
| Joystick gauche | Joystick gauche (identique) |
| Joystick droite | Joystick droite (identique) |
| Boutons A/B/C | ×/○/△ (ou A/B/Y) |
| Gâchettes L1/R1 | L1/R1 (identique) |
| 5 moteurs arc | Vibration unique du gamepad (intensité = moteur central) |
| Start/Select | Start/Select (identique) |

**Pour le haptique**, le gamepad n'a qu'un moteur. Le GamepadMapper simule les 5 moteurs en arc par :
- Vibration unique pour tout contact de bâton
- Logs console indiquant quel moteur NATHAN serait activé (pour debug)
- La validation réelle des 5 moteurs se fait à la Phase 3 (intégration)

#### Stratégie B — Développement audio PC-first (découple AUD ↔ ELEC)

Le développeur audio ne touche **jamais** à l'ESP32-S3 avant la Phase 3. Tout le développement HRTF se fait sur PC :

```
Phase 1 : Recherche + prototypage PC (C/C++ + miniaudio ou libsoundio)
Phase 2 : Module audio spatial fonctionnel sur PC, testé au casque
Phase 3 : Portage vers ESP32-S3, benchmark CPU/latence
Phase 3b: Décision : software pur OU ajout DSP matériel externe
```

L'interface entre le game engine et le module audio est un **contrat** défini dès la Phase 0 (voir 5.3). Tant que le contrat est respecté, les implémentations PC et ESP32 sont interchangeables.

#### Stratégie C — Contrats d'interface (découple toutes les équipes)

Avant tout développement, les équipes définissent ensemble les **interfaces contractuelles** entre les modules. Chaque interface a une **implémentation stub** qui permet de tester sans dépendance.

### 5.3 Contrats d'interface (Phase 0 — à définir en priorité)

Les 5 contrats suivants sont les **premiers livrables du projet**. Ils doivent être définis et validés par toutes les équipes avant le début du développement.

#### Contrat 1 — InputMapper (ENG ↔ ELEC)

```c
// Abstraction des entrées : toute source d'input implémente cette interface
typedef struct {
    float left_x, left_y;     // Joystick gauche (-1.0 à 1.0)
    float right_x, right_y;   // Joystick droite (-1.0 à 1.0)
    bool buttons[9];           // A, B, C, L1, R1, L2, R2, Start, Select
    bool left_click;           // Joystick gauche appuyé
    bool right_click;          // Joystick droite appuyé
} InputState;

void input_mapper_init(void);
InputState input_mapper_read(void);
```

#### Contrat 2 — SpatialAudioEngine (ENG ↔ AUD)

```c
// Abstraction audio : le game engine place des sons, l'implémentation les rend binauraux
typedef int SoundHandle;

void spatial_audio_init(int sample_rate, int max_sources);
void spatial_audio_shutdown(void);

SoundHandle spatial_audio_play(const char* wav_path, float x, float y, float z, bool loop);
void spatial_audio_stop(SoundHandle h);
void spatial_audio_set_position(SoundHandle h, float x, float y, float z);
void spatial_audio_set_volume(SoundHandle h, float vol);

void spatial_audio_update_listener(float px, float py, float orientation_deg);
void spatial_audio_render(int16_t* stereo_buffer, int frame_count);

// Ambiance (non spatialisé, stéréo direct)
void spatial_audio_play_ambient(const char* wav_path, float volume);
void spatial_audio_stop_ambient(void);
```

**Implémentations prévues :**

| Implémentation | Utilisée par | Phase | Backend |
|----------------|-------------|-------|---------|
| `StubAudio` | ENG | Phase 1 | Pas de son, logs console uniquement |
| `PCAudio` | AUD, JEU | Phase 1-2 | `miniaudio` + HRTF sur PC |
| `ESP32Audio` | Tous | Phase 3+ | I2S + PCM5102A + HRTF embarqué |

#### Contrat 3 — HapticEngine (ENG ↔ ELEC)

```c
// Abstraction haptique : 5 moteurs logiques en arc
// Motor IDs : 0=extrême gauche, 1=gauche, 2=centre, 3=droite, 4=extrême droite

void haptic_init(void);
void haptic_pulse(int motor_id, float intensity, int duration_ms);
  // motor_id: 0-4, intensity: 0.0-1.0
void haptic_sweep(float direction, float intensity);
  // direction: -1.0 (gauche) → 1.0 (droite)
void haptic_pattern(const char* pattern_name);
  // Patterns prédéfinis: "cane_wall", "cane_floor", "cane_sweep", "hit", "strum"
void haptic_stop_all(void);
```

**Implémentations prévues :**

| Implémentation | Phase | Comportement |
|----------------|-------|--------------|
| `StubHaptic` | Phase 1 | Logs console uniquement |
| `GamepadHaptic` | Phase 1-2 | Vibration unique du gamepad USB |
| `NathanHaptic` | Phase 3+ | 5 moteurs PWM réels via GPIO ESP32-S3 |

#### Contrat 4 — StorageProvider (ENG)

```c
void storage_init(void);
bool storage_file_exists(const char* path);
int  storage_read_file(const char* path, uint8_t* buffer, int max_size);
int  storage_write_file(const char* path, const uint8_t* data, int size);
char** storage_list_dir(const char* path, int* count);
```

#### Contrat 5 — MiniGameRunner (ENG)

```c
typedef struct {
    char title[64];
    char author[32];
    char description[128];
} MiniGameMeta;

bool minigame_load(const char* dir_path);
MiniGameMeta minigame_get_meta(void);
bool minigame_setup(void);
bool minigame_loop(void);  // retourne false quand le mini-jeu se termine
void minigame_unload(void);
```

### 5.4 Matrice de responsabilité (RACI)

| Livrable | ELEC | ENG | AUD | JEU |
|----------|------|-----|-----|-----|
| Schéma / PCB ESP32-S3 | **R** | C | — | — |
| Boîtier v2.0 (SolidWorks) | **R** | C | — | — |
| Soudure et validation matérielle | **R** | — | — | — |
| Contrats d'interface (Phase 0) | C | **R** | C | I |
| InputMapper (toutes implémentations) | C | **R** | — | — |
| Game engine (scènes, collisions, bâton) | — | **R** | — | I |
| Pipeline HRTF (recherche + implémentation) | — | I | **R** | — |
| Portage audio ESP32-S3 | C | I | **R** | — |
| Intégration MicroPython | — | **R** | — | I |
| Design des pièces du jeu | — | I | I | **R** |
| Banque de sons et musiques | — | — | C | **R** |
| Narration audio (voix Nathan) | — | — | — | **R** |
| Mécaniques guitare/batterie | — | C | C | **R** |
| Tests d'intégration finale | C | **R** | C | C |
| Tests utilisateur (personne DV) | I | C | C | **R** |

> **R** = Responsable, **C** = Consulté, **I** = Informé

---

## 6. Spécifications hardware (v2.0)

### 6.1 Microcontrôleur — ESP32-S3

| Paramètre | Valeur |
|-----------|--------|
| Modèle | ESP32-S3 (module avec PSRAM) |
| Cœurs | 2x Xtensa LX7 @ 240 MHz |
| RAM | 512 KB SRAM + 8 MB PSRAM (externe) |
| Flash | 16 MB (minimum recommandé) |
| ADC | 20 canaux (12 bits) |
| I2S | 2x interfaces I2S |
| USB | USB OTG natif (USB-HID / CDC) |
| Wi-Fi | 802.11 b/g/n 2.4 GHz |
| Bluetooth | BT 5.0 + BLE |

**Justification du choix :** L'ESP32-S3 est le seul microcontrôleur de la gamme ESP32 offrant simultanément USB OTG natif (pour la connexion à l'IDE), suffisamment de RAM pour le HRTF temps réel, et deux interfaces I2S pour l'audio stéréo de haute qualité.

### 6.2 Système audio

#### DAC audio

| Paramètre | Valeur |
|-----------|--------|
| Puce DAC | PCM5102A (Texas Instruments) |
| Interface | I2S |
| Résolution | 32 bits / 384 kHz max |
| SNR | 112 dB |
| Sortie | Jack stéréo 3.5mm (casque uniquement) |
| Amplificateur | Intégré dans PCM5102A (ligne) |

**Note importante :** Le jeu est conçu pour une écoute au **casque stéréo uniquement**. Le son spatial binaural (HRTF) requiert un casque pour l'effet 3D.

#### Pipeline audio spatial

```
Positions 3D des sons (via SpatialAudioEngine)
        ↓
Calcul azimut/élévation/distance
        ↓
Application HRTF (lookup table, MIT KEMAR ou équivalent open-source)
        ↓
Mix audio binaural (canal L + canal R)
        ↓
Buffer DMA → I2S → PCM5102A → Jack 3.5mm
```

#### Format audio des assets

- Samples : **WAV 16 bits, 44.1 kHz, mono** (le moteur applique la spatialisation)
- Musiques d'ambiance : **WAV 16 bits, 44.1 kHz, stéréo** (non spatiales, lecture directe)
- Stockage sur carte micro SD

### 6.3 Système haptique — 5 moteurs en arc

#### Topologie

Les 5 moteurs vibrants sont disposés en arc de cercle dans le corps de la manette :

```
Position physique :  [M0]  [M1]  [M2]  [M3]  [M4]
Direction simulée :  ←←   ←     ↑     →     →→
```

#### Spécifications moteurs

| Paramètre | Valeur |
|-----------|--------|
| Type | Moteur à vibration excentrique (ERM) ou LRA |
| Tension nominale | 3V |
| Contrôle | PWM individuel par canal (intensité variable) |
| Driver | MOSFET N-CH par moteur (ex: 2N7002) OU DRV2605L (recommandé) |
| Fréquence PWM | 1 kHz minimum |

#### Cas d'usage

| Interaction | Moteurs activés | Pattern |
|-------------|-----------------|---------|
| Bâton touche mur à gauche | M0, M1 | Impulsion courte, forte |
| Bâton touche sol | M0 à M4 (tous, faible) | Vibration continue faible |
| Bâton touche obstacle à droite | M3, M4 | Impulsion courte, forte |
| Coup de bâton en combat | M0 à M4 (séquence) | Sweep directionnel |
| Guitare — strumming | M2, M3 | Vibration rhythmique |
| Drum — impact | M correspondant à la zone | Impulsion forte courte |

### 6.4 Entrées utilisateur

#### Joysticks

| Paramètre | Valeur |
|-----------|--------|
| Quantité | 2 (gauche + droite) |
| Type | Joystick analogique double axe (modèle Xbox/PS) |
| Résolution ADC | 12 bits (0–4095) |
| Canaux requis | 4 entrées ADC (X/Y par joystick) |
| Bouton intégré | Oui (appui joystick = bouton numérique) |

#### Boutons

| Bouton | Type | Usage principal |
|--------|------|-----------------|
| A (×) | Arcade 30mm | Action principale |
| B (○) | Arcade 30mm | Action secondaire |
| C (△) | Arcade 30mm | Action tertiaire / menu |
| L1 | Micro switch | Gâchette gauche |
| R1 | Micro switch | Gâchette droite |
| Start | Bouton tactile | Menu / pause |
| Select | Bouton tactile | Retour / annuler |

### 6.5 Alimentation

| Paramètre | Valeur |
|-----------|--------|
| Batterie | LiPo 1S (3.7V) — capacité min. 2000 mAh |
| Connecteur de charge | USB-C |
| Circuit de charge | TP4056 ou MCP73831 |
| Protection | Surcharge, décharge profonde, court-circuit |
| Régulateur | LDO 3.3V (ex: AMS1117-3.3) pour ESP32-S3 |
| Autonomie cible | ≥ 8 heures |

**Estimation de consommation :**
- ESP32-S3 actif : ~240 mA max
- PCM5102A : ~10 mA
- 5 moteurs (pic simultané max) : ~5 × 150 mA = 750 mA
- Total pic : ~1A → batterie 2000 mAh ≈ 2h en pic, ~6-8h en usage normal

### 6.6 Connectivité

| Interface | Usage |
|-----------|-------|
| USB-C | Charge + connexion à l'IDE Cantante (USB CDC) |
| Wi-Fi 2.4 GHz | Mise à jour OTA (optionnel v2.0) |
| Micro SD | Stockage assets audio, jeux, mini-jeux |

### 6.7 Boîtier (refonte ergonomique)

#### Contraintes de refonte

- Intégrer 2 joysticks (gauche + droite)
- Intégrer 5 moteurs en arc dans les poignées
- Passer à une batterie LiPo + port USB-C
- Conserver l'inspiration Xbox pour l'ergonomie
- Rester fabricable par impression 3D FDM
- **Dimensions maximales :** Tenir dans une main adulte (largeur ~16 cm)

#### Fichiers à mettre à jour

- `CAD_Files/Console/NATHAN-console-asm.SLDASM` — refonte complète
- `CAD_Files/Console/parts/*.SLDPRT` — toutes les pièces
- `3D Print Models/*.STL` — regenerer depuis les nouveaux SLDPRT
- `CAD_Files/PCB/` — nouveau schéma et PCB pour ESP32-S3

---

## 7. Spécifications firmware et logiciel bas niveau

### 7.1 Environnement de développement

| Paramètre | Valeur |
|-----------|--------|
| SDK | ESP-IDF v5.x (officiel Espressif) |
| Langage principal | C / C++17 |
| Build system | CMake |
| IDE recommandé | VSCode + extension ESP-IDF |
| Débogage | JTAG via USB (ESP32-S3 supporte le JTAG USB natif) |
| Tests | Unity test framework (embarqué) |

### 7.2 Architecture firmware

```
┌─────────────────────────────────────────────────────────┐
│                      APPLICATION                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Game Engine │  │ MicroPython  │  │   USB Bridge   │  │
│  │   (C/C++)   │  │  Sandbox     │  │   (CDC)        │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         └────────────────┴──────────────────┘            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Contrats d'interface (section 5.3)          │ │
│  │  InputMapper | SpatialAudioEngine | HapticEngine    │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Hardware Abstraction Layer (HAL)        │ │
│  │  NathanMapper | ESP32Audio | NathanHaptic | Storage │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │ ESP-IDF  │ │FreeRTOS│ │  I2S   │ │  SPI   │          │
│  └──────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
```

### 7.3 Tâches FreeRTOS

| Tâche | Priorité | Core | Rôle |
|-------|----------|------|------|
| `task_audio_render` | Très haute | Core 0 | Rendu HRTF + DMA I2S |
| `task_game_logic` | Haute | Core 1 | Logique de jeu, état |
| `task_input_poll` | Haute | Core 1 | Lecture entrées via InputMapper à 100 Hz |
| `task_haptic_ctrl` | Moyenne | Core 1 | Contrôle moteurs via HapticEngine |
| `task_usb_bridge` | Basse | Core 1 | Communication USB avec IDE Cantante |
| `task_sd_io` | Basse | Core 0 | Lecture assets depuis SD |

### 7.4 Protocole USB CDC (pont avec l'IDE Cantante)

Le firmware expose un port série virtuel (USB CDC) avec un protocole simple :

| Commande | Direction | Description |
|----------|-----------|-------------|
| `LIST` | IDE → Console | Lister les mini-jeux sur SD |
| `UPLOAD <path> <size>` | IDE → Console | Envoyer un fichier vers SD |
| `DELETE <path>` | IDE → Console | Supprimer un fichier sur SD |
| `LOG` | Console → IDE | Stream des logs/erreurs en temps réel |
| `META <path>` | IDE → Console | Lire les métadonnées d'un mini-jeu |

> C'est l'unique point de contact entre ce projet et Cantante. Tant que ce protocole est respecté, les deux projets évoluent indépendamment.

### 7.5 Support MicroPython embarqué

Le firmware intègre un interpréteur **MicroPython** via la bibliothèque `micropython-embed` compilée en tant que composant ESP-IDF.

**Note de continuité :** Le jeu existant GlassBreaker tourne en CircuitPython sur Pico. MicroPython et CircuitPython partagent la même syntaxe Python et des APIs très proches — le passage à MicroPython pour v2.0 est transparent pour les mini-jeux.

- Les mini-jeux sont des fichiers `.py` sur la carte SD (dossier `/sd/minigames/`)
- L'interpréteur est lancé dans un contexte sandboxé avec accès limité aux APIs HAL
- Un module C expose l'API du moteur à MicroPython :
  - `nathan.audio.play(sound_id, x, y, z)`
  - `nathan.haptic.pulse(motor, intensity)`
  - `nathan.input.read_joystick(id)` → `(x, y)`
  - `nathan.input.read_button(id)` → `bool`
- Les sons des mini-jeux sont stockés dans `/sd/minigames/<nom_jeu>/sounds/`

---

## 8. Spécifications du game engine

### 8.1 Philosophie du moteur

Le moteur est conçu pour un jeu **entièrement auditif**. Il n'y a pas de rendu graphique. Le "monde" est une grille 2D avec une coordonnée de hauteur. Les sons sont les seuls retours d'état du monde.

**Toute interaction avec le hardware passe par les contrats d'interface (section 5.3).** Le game engine n'appelle jamais directement I2S, GPIO, ou ADC.

### 8.2 Représentation du monde

#### Espace de coordonnées

```
        Y (profondeur)
        ^
        |
        |    * Son à (x=2, y=3, z=1)
        |
        +----------→ X (droite/gauche)

Z = hauteur (sol=0, plafond=3m env.)
Joueur toujours à Z=0 (sol)
```

- Grille 2D en centimètres entiers
- Hauteur Z flottante (0.0 à 3.0 m typiquement)
- Le joueur a une position `(px, py)` et une orientation `θ` (angle en degrés)

#### Calcul HRTF (responsabilité de l'équipe AUD)

Pour chaque source sonore à `(sx, sy, sz)` avec le joueur en `(px, py)` orienté à `θ` :

```
dx = sx - px
dy = sy - py
distance = sqrt(dx² + dy² + sz²)
azimut = atan2(dy, dx) - θ   (relatif à l'orientation du joueur)
élévation = atan2(sz, sqrt(dx² + dy²))
```

Application d'une HRTF lookup table (MIT KEMAR dataset, open-source, 187 positions) :
- Sélection des 2 HRTF les plus proches par interpolation
- Atténuation par distance : `gain = 1 / (1 + distance * k)`
- Rendu stéréo par convolution avec les réponses impulsionnelles HRTF gauche/droite

> **Note équipe AUD :** Le game engine fournit les positions via `spatial_audio_update_listener()` et `spatial_audio_set_position()`. Le calcul HRTF est entièrement encapsulé dans le module audio. L'équipe AUD est libre de choisir l'algorithme, la taille des filtres, et l'implémentation tant que l'API du contrat 2 est respectée.

### 8.3 API du game engine

```cpp
// Gestion de scène
Scene* scene_create(const char* name);
void scene_load(Scene* s);
void scene_unload(Scene* s);

// Entités sonores (délègue au SpatialAudioEngine)
SoundEntity* entity_create(float x, float y, float z, const char* sound_file);
void entity_set_position(SoundEntity* e, float x, float y, float z);
void entity_set_looping(SoundEntity* e, bool loop);
void entity_play(SoundEntity* e);
void entity_stop(SoundEntity* e);

// Joueur
void player_set_position(float x, float y);
void player_set_orientation(float angle_deg);
void player_move(float dx, float dy);

// Collisions (murs/obstacles)
void world_add_wall(float x1, float y1, float x2, float y2);
bool world_check_collision(float x, float y, float radius);

// Audio ambiant (non spatial, via SpatialAudioEngine)
void ambient_play(const char* sound_file, float volume);
void ambient_stop();

// Haptique (délègue au HapticEngine)
void engine_haptic_cane(float contact_x, float contact_y);
```

### 8.4 Système de collisions et bâton

Le bâton d'aveugle est simulé comme un **rayon** (raycast) partant du joueur dans la direction du joystick droit.

```
Joueur (px, py)
      \
       \  ← direction joystick droit
        \
         * point de contact (cx, cy)
         |
         | MURS ou OBSTACLES
```

- La distance au contact détermine l'intensité de vibration (proche = plus fort)
- La direction du contact (gauche/droite/avant) détermine quels moteurs activés
- Le son de frottement change selon la surface (bois, béton, herbe) via le tag de surface du mur

---

## 9. Spécifications du premier jeu — La Maison de Nathan

### 9.1 Concept général

**Titre :** La Maison de Nathan
**Genre :** Jeu de vie / exploration sensorielle
**Perspective :** Première personne sonore (FPS audio)
**Durée :** Jeu ouvert (exploration libre + quêtes)

Le joueur incarne **Nathan**, un adolescent aveugle. Il doit accomplir des tâches quotidiennes, explorer sa maison, jouer de la musique, aller à l'école, et affronter des adversaires imaginaires avec son bâton.

### 9.2 Structure de la maison

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │
│  │  CUISINE │  │  SALON   │  │    CHAMBRE     │    │
│  │          │  │  (HUB)   │  │                │    │
│  └──────────┘  └────┬─────┘  └────────────────┘    │
│                     │                               │
│  ┌──────────┐  ┌────┴─────┐  ┌────────────────┐    │
│  │ SALLE DE │  │          │  │  SALLE DE      │    │
│  │ MUSIQUE  │  │ COULOIR  │  │  MINI-JEUX     │    │
│  │          │  │          │  │                │    │
│  └──────────┘  └────┬─────┘  └────────────────┘    │
│                     │                               │
│             ┌───────┴──────┐                        │
│             │    ÉCOLE     │                        │
│             │  (extérieur) │                        │
│             └──────────────┘                        │
└─────────────────────────────────────────────────────┘
```

### 9.3 Pièce 1 — Le Salon (Hub principal)

**Rôle :** Point de départ et hub de navigation.

**Audio :** Musique d'ambiance douce (genre lo-fi / jazz calme). Sons de la maison : horloge, ventilation, sons extérieurs filtrés.

**Gameplay :**
- Premier endroit où le joueur apprend à se déplacer avec le joystick gauche
- Apprentissage de la navigation au son (chaque pièce a une signature musicale)
- Tutoriel intégré au jeu (voix de Nathan explique ses sens)

**Éléments interactifs :**
- Canapé (son d'assise)
- Téléviseur (son — Nathan écoute un programme audio)
- Fenêtre (sons extérieurs, météo)

### 9.4 Pièce 2 — La Cuisine

**Audio :** Musique rythmée type jazz. Sons de cuisine (réfrigérateur, eau, vaisselle).

**Mini-jeu principal : Faire à manger**
- Objectif : Suivre une recette audio étape par étape
- Mécanique : Les joysticks imitent des gestes culinaires (mélanger = rotation joystick gauche, couper = up/down joystick droit)
- Feedback haptique : résistance simulée selon la texture des aliments
- Succès/échec évalué par la précision du geste et le timing

**Éléments interactifs :**
- Réfrigérateur (inventaire d'ingrédients, son caractéristique)
- Casserole (sons de cuisson évolutifs)
- Robinet (son de l'eau)

### 9.5 Pièce 3 — La Chambre

**Audio :** Musique calme / ASMR. Sons de chambre (ventilateur, pluie sur la fenêtre, horloge).

**Mini-jeux :**
- **Se lever le matin :** réveil, s'habiller (séquence de boutons au son)
- **Exploration libre :** Fouiller les tiroirs, découvrir des souvenirs audio

**Éléments interactifs :**
- Lit (point de sauvegarde)
- Radio (change la musique d'ambiance)
- Bureau (accès aux devoirs — mini-jeu de mémorisation sonore)

### 9.6 Pièce 4 — La Salle de Musique

**Audio :** Selon l'instrument joué. Réverbération de pièce simulée.

#### Instrument 1 — La Guitare

| Contrôle | Action |
|----------|--------|
| Joystick gauche (vertical) | Sélection de case (montée/descente sur le manche) |
| Joystick gauche (horizontal) | Sélection de corde |
| Joystick droit (vertical rapide ↓) | Strum vers le bas |
| Joystick droit (vertical rapide ↑) | Strum vers le haut |
| Bouton A | Accord de base (accord ouvert) |
| Bouton B | Accord barré |
| Bouton C | Accord spécial / sustain |

**Sons :** Samples de guitare acoustique réelle (banque de sons, licence libre).
**Feedback haptique :** Vibration légère des moteurs à chaque strum.

#### Instrument 2 — La Batterie

| Contrôle | Action |
|----------|--------|
| Joystick gauche ↑ | Grosse caisse (kick drum) |
| Joystick gauche ↓ | Charleston fermé (hi-hat closed) |
| Joystick gauche ← | Tom basse |
| Joystick gauche → | Tom aigu |
| Joystick droit ↑ | Snare |
| Joystick droit ↓ | Charleston ouvert (hi-hat open) |
| Gâchette L1 | Cymbale crash gauche |
| Gâchette R1 | Cymbale crash droite |
| Joystick droit appuyé | Ride cymbal |

**Sons :** Samples de batterie acoustique (banque libre).
**Feedback haptique :** Impact fort et court sur le/les moteurs correspondants.

**Mode enregistrement :** Possibilité d'enregistrer une séquence et de la rejouer (sequencer simple).

### 9.7 Pièce 5 — La Salle de Mini-Jeux

**Audio :** Musique arcade 8-bit. Sons d'ordinateur/console.

**Gameplay :**
- Hub des mini-jeux créés par l'utilisateur via l'IDE Cantante
- Nathan s'assoit à son poste et peut lancer un mini-jeu de la liste sur la carte SD
- Navigation dans la liste par audio (lecture du titre depuis les métadonnées)
- Retour au salon après fin d'un mini-jeu

### 9.8 Zone 6 — L'École (extérieur)

**Audio :** Sons de rue, bruits urbains, cour d'école, voix des camarades.

**Mécanique principale : Navigation avec le bâton**

C'est ici que le bâton d'aveugle est le contrôle primaire :
- **Joystick droit** : contrôle la direction du bâton (360°)
- Le raycast détecte obstacles, bordures de trottoir, portes
- Les **5 moteurs** donnent la direction du contact
- Le **son** de frappe change selon la surface

**Sous-zones de l'école :**
- Trajet aller (navigation en rue — obstacles mobiles : piétons)
- Cour de récréation (interactions sociales audio avec personnages)
- Salle de classe (mini-jeux pédagogiques : maths, mémoire, musique)

**Combats imaginaires :**
- Déclenchés optionnellement dans certaines zones
- Le bâton devient arme : mêmes contrôles, adversaires signalés par sons directionnels
- Détection de coup : le raycast touche un ennemi → impact fort + son
- L'ennemi riposte → vibration directionnelle + son d'attaque (le joueur peut parer)

### 9.9 Contrôles de déplacement global

| Contrôle | Action |
|----------|--------|
| Joystick gauche | Déplacement du personnage (marche/direction) |
| Joystick droit | Direction du bâton (mode bâton) / action contextuelle |
| Bouton A | Interagir / confirmer |
| Bouton B | Annuler / reculer |
| Bouton C | Menu contextuel de la pièce |
| Start | Menu pause |
| L1 | Mode bâton (activer/désactiver bâton) |
| R1 | Sprint |

### 9.10 Système de navigation sonore inter-pièces

Chaque pièce émet une **signature musicale** différente. Depuis le couloir, les musiques des pièces adjacentes sont audibles en spatialisation. Plus le joueur approche d'une porte, plus la musique de la pièce correspondante est forte et plus son positionnement directionnel est précis.

---

## 10. Système de mini-jeux

### 10.1 Architecture générale

```
┌─────────────────────┐         ┌─────────────────────────┐
│     PC / Mac        │  USB-C  │      ESP32-S3           │
│                     │◄───────►│                         │
│  IDE Cantante       │ (CDC)   │  MiniGameRunner         │
│  (développé         │         │  ┌──────────────────┐   │
│   séparément)       │         │  │  mini_game.py    │   │
│                     │         │  │                  │   │
│                     │         │  │  nathan.audio    │   │
│                     │         │  │  nathan.haptic   │   │
│                     │         │  │  nathan.input    │   │
│                     │         │  └──────────────────┘   │
└─────────────────────┘         └─────────────────────────┘
```

> L'IDE Cantante est développé dans un dépôt séparé et sera intégré sous `ide/` une fois le protocole USB CDC (section 7.4) stabilisé. Le développement de Cantante n'apparaît pas dans la planification de ce cahier des charges.

### 10.2 API MicroPython exposée aux mini-jeux

```python
import nathan

# Audio spatial
nathan.audio.play(sound_id: str, x: float, y: float, z: float = 0.0)
nathan.audio.stop(sound_id: str)
nathan.audio.set_ambient(sound_id: str)

# Haptique
nathan.haptic.pulse(motor: int, intensity: float, duration_ms: int)
  # motor: 0-4 (gauche à droite)
  # intensity: 0.0 à 1.0
nathan.haptic.sweep(direction: float, intensity: float)
  # direction: -1.0 (gauche) à 1.0 (droite)

# Entrées
x, y = nathan.input.joystick(id: int)  # id: 0=gauche, 1=droite
pressed = nathan.input.button(id: int)  # id: 0=A, 1=B, 2=C, 3=L1, 4=R1

# Contrôle du jeu
nathan.game.score(points: int)
nathan.game.end(success: bool)
nathan.game.set_title(title: str)

# Utilitaires
nathan.sleep_ms(ms: int)  # attente non bloquante
nathan.time_ms() -> int   # temps depuis démarrage
```

### 10.3 Format de mini-jeu

Le format est **directement inspiré** de l'architecture GlassBreaker existante (`game/menu.py`). Un mini-jeu est une **classe Python** avec métadonnées et méthodes standardisées.

```python
# Structure d'un mini-jeu NATHAN (MicroPython)
import nathan

META = {
    "title": "Mon Mini-Jeu",          # Lu à voix haute dans le hub
    "author": "Arthur",
    "description": "Un jeu de mémoire sonore"
}

class MonMiniJeu:
    def __init__(self):
        self.score = 0

    def setup(self):
        """Appelé une fois au démarrage."""
        nathan.audio.set_ambient("arcade_ambient.wav")
        nathan.audio.play("intro.wav", 0, 0, 0)

    def loop(self) -> bool:
        """
        Appelé à chaque frame.
        Retourne True pour continuer, False pour terminer.
        """
        x, y = nathan.input.joystick(0)
        if nathan.input.button(0):   # Bouton A
            nathan.audio.play("confirm.wav", 0, 0, 0)
            nathan.haptic.pulse(2, 0.8, 100)
            self.score += 1
        if self.score >= 10:
            nathan.game.end(success=True)
            return False
        return True

# Point d'entrée appelé par le MiniGameRunner
def create():
    return MonMiniJeu()
```

**Structure de fichiers sur la carte SD :**
```
/sd/minigames/
└── mon_mini_jeu/
    ├── main.py          # Fichier principal (contient META + classe)
    └── sounds/          # Sons du mini-jeu (WAV 16 bits, 44.1kHz, mono)
        ├── intro.wav
        ├── confirm.wav
        └── arcade_ambient.wav
```

---

## 11. Contraintes et risques techniques

### 11.1 Risques majeurs

#### Risque R1 — HRTF temps réel sur ESP32-S3 (CRITIQUE)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Critique |
| Description | Le rendu HRTF temps réel (convolution) est très coûteux en CPU. Avec plusieurs sources simultanées, l'ESP32-S3 pourrait atteindre ses limites. |
| Impact | Latence audio, artifacts, ou limitation du nombre de sons simultanés |
| Mitigation 1 | Utiliser des HRTF avec réponses impulsionnelles courtes (128 samples au lieu de 512) |
| Mitigation 2 | Limiter à 4-6 sources sonores spatiales simultanées |
| Mitigation 3 | Pré-calculer les positions pour les sons statiques (bake offline) |
| Mitigation 4 | En fallback, audio stéréo simple (panoramique L/R) sans HRTF si charge trop haute |
| Responsable | Équipe AUD — décision à prendre à la Phase 2 après benchmark PC et ESP32 |

#### Risque R2 — Autonomie batterie (ÉLEVÉ)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Élevé |
| Description | 5 moteurs + ESP32-S3 actif + DAC = consommation pic ~1A |
| Mitigation | Gérer l'activation des moteurs (jamais tous 5 en continu), sleep du Wi-Fi quand inutile, 2500 mAh minimum |
| Responsable | Équipe ELEC |

#### Risque R3 — MicroPython sur ESP32-S3 (MOYEN)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Moyen |
| Description | L'intégration de MicroPython comme composant ESP-IDF en parallèle du game engine C++ est complexe |
| Mitigation | Utiliser `micropython-embed`, dédier le Core 0 au game engine et le Core 1 à l'interpréteur MicroPython |
| Responsable | Équipe ENG |

#### Risque R4 — Ergonomie boîtier avec 2 joysticks (MOYEN)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Moyen |
| Description | La refonte mécanique est importante. Le boîtier v1.0 ne supporte pas 2 joysticks. |
| Mitigation | Prototype en impression 3D rapide, validation ergonomique avant fabrication finale |
| Responsable | Équipe ELEC |

#### Risque R5 — Désynchronisation entre équipes (ÉLEVÉ)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Élevé |
| Description | Les 4 équipes travaillent en parallèle. Si les contrats d'interface ne sont pas respectés ou changent en cours de route, l'intégration (Phase 3) devient chaotique. |
| Impact | Retards majeurs à l'intégration, bugs d'interface, rework |
| Mitigation 1 | **Phase 0 obligatoire** : valider les contrats d'interface ensemble avant tout code |
| Mitigation 2 | **Points de synchronisation** fixes (SYNC 1, 2, 3) avec intégration incrémentale |
| Mitigation 3 | **Tests d'interface** : chaque implémentation est testée contre un stub de l'autre côté |
| Mitigation 4 | **Gel des interfaces** après Phase 0. Tout changement d'interface requiert l'accord des deux équipes impactées |
| Responsable | Chef de projet / toutes les équipes |

### 11.2 Contraintes techniques reconnues

- ESP32-S3 : RAM totale 8 MB PSRAM — les HRTF lookup tables MIT KEMAR prennent ~1 MB, laisser ~6 MB pour le moteur et les samples audio en buffer
- Micro SD : Latence de lecture (~few ms) — les samples audio doivent être pré-chargés en RAM avant lecture
- MicroPython : Vitesse d'exécution ~10-50x plus lente que C — les mini-jeux sont des jeux simples, pas de physique complexe
- PCM5102A : Pas de contrôle de volume hardware — le volume doit être géré par software

---

## 12. Planification par workstreams et dépendances

### 12.1 Vue d'ensemble — 4 workstreams parallèles

```
Semaines    1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
            │           │  SYNC 1     │              │  SYNC 2     │              │  SYNC 3
            │           │  (sem 6)    │              │  (sem 14)   │              │  (sem 22)
            │           │             │              │             │              │
Phase 0:    ██          │             │              │             │              │
(toutes)    │           │             │              │             │              │
            │           │             │              │             │              │
ELEC:       ░░ ████████████████ ░░░░░████████████████░░░░░░████████░░░░░░░░░░░░░░│
            │  Schéma+PCB      Fab   Soudure+Test   │  Boîtier    │              │
            │           │             │              │             │              │
ENG:        ░░ ████████████████████████████████████████████████████████████████████
            │  Mapper+HAL stubs Scènes+Collisions   │  MicroPy    │  Intégration │
            │           │             │              │             │              │
AUD:        ░░ ████████████████████████████████████████████████████░░░░░░░░░░░░░░│
            │  Recherche HRTF  Proto PC│  Benchmark  │  Portage    │              │
            │           │             │  ESP32       │  ESP32      │              │
            │           │             │              │             │              │
JEU:        ░░ ░░░░████████████████████████████████████████████████████████████████
            │     Design+Sons  Salon+Cuisine+Chambre │  Musique+École│  Polish    │
```

### 12.2 Phase 0 — Contrats d'interface et setup (semaines 1-2)

**Durée :** 2 semaines
**Équipes :** TOUTES
**Objectif :** Aligner toutes les équipes, figer les interfaces, préparer l'environnement.

| ID | Tâche | Responsable | Dépendances | Priorité |
|----|-------|-------------|-------------|----------|
| P0.1 | Rédiger et valider le contrat InputMapper | ENG + ELEC | — | Critique |
| P0.2 | Rédiger et valider le contrat SpatialAudioEngine | ENG + AUD | — | Critique |
| P0.3 | Rédiger et valider le contrat HapticEngine | ENG + ELEC | — | Critique |
| P0.4 | Rédiger et valider le contrat StorageProvider | ENG | — | Critique |
| P0.5 | Rédiger et valider le contrat MiniGameRunner | ENG | — | Critique |
| P0.6 | Acheter 2-3 manettes USB (DualShock/Xbox) pour dev | ENG | — | Critique |
| P0.7 | Acheter ESP32-S3 DevKit + PCM5102A module (pour ELEC et AUD) | ELEC | — | Critique |
| P0.8 | Setup repo : structure dossiers `firmware/`, `engine/`, `game/`, `audio/` | ENG | — | Haute |
| P0.9 | Setup ESP-IDF + CMake + premier build vide | ENG | P0.8 | Haute |
| P0.10 | Document de conventions (nommage, coding style, format WAV, arborescence SD) | TOUTES | — | Haute |

**Jalon Phase 0 :** Contrats validés et signés par toutes les équipes. Matériel commandé.

---

### 12.3 Workstream ELEC — Manette physique

**Responsable :** Équipe génie électrique
**Indépendant de :** ENG, AUD, JEU (aucune dépendance bloquante après Phase 0)

| ID | Tâche | Semaines | Dépendances | Priorité |
|----|-------|----------|-------------|----------|
| ELEC.1 | Breadboard ESP32-S3 + PCM5102A : valider I2S audio | 2-4 | P0.7 | Critique |
| ELEC.2 | Breadboard 5 moteurs PWM : valider contrôle intensité | 2-4 | P0.7 | Critique |
| ELEC.3 | Breadboard 2 joysticks ADC : valider lecture | 2-4 | P0.7 | Haute |
| ELEC.4 | Breadboard alimentation LiPo + USB-C charge | 3-5 | P0.7 | Haute |
| ELEC.5 | Schéma KiCAD v2.0 complet | 4-7 | ELEC.1-4 | Critique |
| ELEC.6 | PCB KiCAD v2.0 layout + DRC | 6-8 | ELEC.5 | Critique |
| ELEC.7 | Commande PCB (JLCPCB/PCBWay) | 8 | ELEC.6 | Critique |
| ELEC.8 | *Attente fabrication PCB (~2 semaines)* | 8-10 | ELEC.7 | — |
| ELEC.9 | Soudure composants PCB v2.0 | 10-11 | ELEC.8 | Critique |
| ELEC.10 | Tests électriques PCB (continuité, tensions, courant) | 11-12 | ELEC.9 | Critique |
| ELEC.11 | Flash firmware de test sur PCB (valider ESP-IDF boot) | 12-13 | ELEC.10, ENG.2 | Critique |
| ELEC.12 | Refonte boîtier SolidWorks v2.0 | 8-14 | ELEC.3, ELEC.2 | Haute |
| ELEC.13 | Impression 3D prototype boîtier | 14-15 | ELEC.12 | Haute |
| ELEC.14 | Assemblage complet : PCB + boîtier + batterie | 15-16 | ELEC.13, ELEC.10 | Haute |
| ELEC.15 | Test ergonomie avec utilisateur | 16-18 | ELEC.14 | Haute |
| ELEC.16 | Mise à jour BOM v2.0 | 7-8 | ELEC.5 | Moyenne |

**Jalons ELEC :**
- **SYNC 1 (sem 6) :** Breadboard fonctionnel, schéma en cours. Fournir aux devs les specs exactes des GPIO/ADC.
- **SYNC 2 (sem 14) :** PCB soudé et testé. Prêt pour flash firmware.
- **SYNC 3 (sem 22) :** Manette complète assemblée (PCB + boîtier + batterie). Prête pour intégration finale.

---

### 12.4 Workstream ENG — Game Engine

**Responsable :** Équipe génie informatique (engine)
**Utilise :** Manette USB de substitution (GamepadMapper) jusqu'à SYNC 3
**Dépend de :** Contrats d'interface (Phase 0)

| ID | Tâche | Semaines | Dépendances | Priorité |
|----|-------|----------|-------------|----------|
| ENG.1 | Implémenter `GamepadMapper` (manette USB → InputState) | 2-3 | P0.1, P0.6 | Critique |
| ENG.2 | Implémenter `StubAudio` (logs sans son) | 2-3 | P0.2 | Critique |
| ENG.3 | Implémenter `StubHaptic` + `GamepadHaptic` | 2-3 | P0.3 | Critique |
| ENG.4 | Implémenter `StorageProvider` (SD card FAT32) | 3-4 | P0.4 | Haute |
| ENG.5 | Implémenter `DebugMapper` (clavier/souris) | 3 | P0.1 | Moyenne |
| ENG.6 | Système de scènes : create/load/unload/transition | 4-6 | ENG.2 | Critique |
| ENG.7 | Représentation monde 2D+Z, gestion entités | 4-6 | — | Critique |
| ENG.8 | Système de collision : murs, obstacles | 5-7 | ENG.7 | Critique |
| ENG.9 | Déplacement joueur (joystick gauche → position + orientation) | 5-7 | ENG.1, ENG.7 | Critique |
| ENG.10 | Bâton d'aveugle : raycast + direction + collision | 7-9 | ENG.8, ENG.9 | Critique |
| ENG.11 | Pont bâton → HapticEngine (contact → moteur directionnel) | 8-10 | ENG.10, ENG.3 | Haute |
| ENG.12 | Pont entités → SpatialAudioEngine (positions → audio) | 8-10 | ENG.7, P0.2 | Haute |
| ENG.13 | *Intégration PCAudio* (remplacer StubAudio par l'implémentation AUD) | 10-11 | ENG.12, AUD.5 | Haute |
| ENG.14 | USB CDC : protocole de communication avec IDE | 10-12 | P0.8 | Haute |
| ENG.15 | Intégration MicroPython (`micropython-embed`) | 12-16 | ENG.4 | Haute |
| ENG.16 | Module `nathan` Python (bridge C → MicroPython) | 14-17 | ENG.15, P0.5 | Haute |
| ENG.17 | MiniGameRunner : loader, sandbox, limites mémoire/temps | 16-18 | ENG.16, ENG.4 | Haute |
| ENG.18 | `NathanMapper` (manette réelle → InputState) | 18-20 | P0.1, ELEC.11 | Critique |
| ENG.19 | `NathanHaptic` (5 moteurs PWM réels) | 18-20 | P0.3, ELEC.11 | Haute |
| ENG.20 | Intégration `ESP32Audio` (module audio final sur ESP32) | 20-22 | AUD.8 | Critique |
| ENG.21 | Tests d'intégration complets sur matériel réel | 22-24 | ENG.18-20, ELEC.14 | Critique |
| ENG.22 | Optimisation et profiling sur ESP32-S3 | 24-26 | ENG.21 | Haute |

**Jalons ENG :**
- **SYNC 1 (sem 6) :** GamepadMapper + stubs fonctionnels. Le game engine tourne sur PC/ESP32 avec manette USB, sans son réel, avec logs haptiques.
- **SYNC 2 (sem 14) :** Scènes, collisions, bâton, déplacement fonctionnels. Audio spatial PC intégré. Le jeu est jouable au casque sur PC avec manette USB.
- **SYNC 3 (sem 22) :** Tout fonctionne sur hardware réel. NathanMapper + NathanHaptic + ESP32Audio intégrés.

---

### 12.5 Workstream AUD — Audio spatial

**Responsable :** 1 développeur spécialisé signal/audio
**Indépendant de :** ELEC (développement entièrement sur PC jusqu'à Phase 3)
**Dépend de :** Contrat SpatialAudioEngine (Phase 0)

| ID | Tâche | Semaines | Dépendances | Priorité |
|----|-------|----------|-------------|----------|
| AUD.1 | Recherche HRTF : évaluer MIT KEMAR, CIPIC, SOFA | 2-4 | P0.2 | Critique |
| AUD.2 | Choix de la bibliothèque audio PC (`miniaudio`, `libsoundio`, ou custom) | 2-3 | — | Critique |
| AUD.3 | Prototype HRTF sur PC : 1 source, convolution basique | 3-5 | AUD.1, AUD.2 | Critique |
| AUD.4 | Multi-sources : mix de 4-6 sources HRTF simultanées | 5-7 | AUD.3 | Critique |
| AUD.5 | `PCAudio` : implémentation complète du contrat SpatialAudioEngine sur PC | 6-9 | AUD.4, P0.2 | Critique |
| AUD.6 | Tests perceptuels au casque (validation immersion) | 8-10 | AUD.5 | Haute |
| AUD.7 | Benchmark ESP32-S3 : portage convolution HRTF, mesure CPU/latence | 10-14 | AUD.5, P0.7 | Critique |
| AUD.8 | **Décision : software pur OU DSP externe** | 14 | AUD.7 | Critique |
| AUD.9a | *(Si software pur)* `ESP32Audio` : implémentation finale I2S + HRTF | 14-20 | AUD.8, ELEC.1 | Critique |
| AUD.9b | *(Si DSP externe)* Sélection puce DSP, intégration I2S ESP32 → DSP → DAC | 14-20 | AUD.8, ELEC.5 | Critique |
| AUD.10 | Optimisation : taille filtre, nombre de sources, latence cible < 20ms | 18-22 | AUD.9 | Haute |
| AUD.11 | Tests sur matériel final (PCB + casque) | 22-24 | AUD.10, ELEC.14 | Haute |

**Jalons AUD :**
- **SYNC 1 (sem 6) :** HRTF prototype PC fonctionnel (1 source). Premiers résultats de spatialisation au casque.
- **SYNC 2 (sem 14) :** `PCAudio` complet, 4-6 sources simultanées sur PC. Benchmark ESP32 en cours. Décision software/DSP prise.
- **SYNC 3 (sem 22) :** `ESP32Audio` fonctionnel sur matériel réel. Prêt pour intégration game engine.

---

### 12.6 Workstream JEU — Contenu et design de jeu

**Responsable :** Équipe contenu / game design
**Utilise :** Game engine (ENG) + PCAudio (AUD) + GamepadMapper sur PC
**Dépend de :** Scènes et collisions de ENG (sem ~6-8)

| ID | Tâche | Semaines | Dépendances | Priorité |
|----|-------|----------|-------------|----------|
| JEU.1 | Design détaillé de la carte de la maison (coordonnées 2D, tailles pièces) | 2-4 | — | Critique |
| JEU.2 | Liste exhaustive des sons nécessaires (ambiances, effets, voix) | 2-4 | — | Critique |
| JEU.3 | Sourcing / enregistrement de la banque de sons | 3-10 | JEU.2 | Critique |
| JEU.4 | Enregistrement narration audio (voix de Nathan, tutoriel) | 6-10 | JEU.1 | Haute |
| JEU.5 | Salon : placement des entités, ambiance, interactions | 7-9 | JEU.1, JEU.3, ENG.6 | Critique |
| JEU.6 | Tutoriel intégré (voix Nathan explique les contrôles) | 8-10 | JEU.5, JEU.4 | Haute |
| JEU.7 | Navigation inter-pièces (signatures musicales par porte) | 8-10 | JEU.5, ENG.12 | Critique |
| JEU.8 | Cuisine : ambiance + mini-jeu "faire à manger" | 9-12 | JEU.3, ENG.9 | Haute |
| JEU.9 | Chambre : ambiance + mini-jeux + point de sauvegarde | 9-12 | JEU.3, ENG.6 | Haute |
| JEU.10 | Salle de musique — guitare (samples + mapping joystick) | 10-14 | JEU.3, ENG.1 | Haute |
| JEU.11 | Salle de musique — batterie (samples + mapping joystick/gâchettes) | 10-14 | JEU.3, ENG.1 | Haute |
| JEU.12 | École — navigation bâton en extérieur | 12-16 | JEU.3, ENG.10 | Haute |
| JEU.13 | École — combats imaginaires | 14-18 | JEU.12, ENG.10 | Moyenne |
| JEU.14 | Salle de mini-jeux (hub, navigation liste) | 16-18 | ENG.17 | Haute |
| JEU.15 | 2-3 mini-jeux d'exemple en MicroPython | 18-20 | ENG.16 | Haute |
| JEU.16 | Tâches quotidiennes additionnelles | 18-22 | JEU.5-JEU.9 | Basse |
| JEU.17 | Polish : équilibrage, transitions, flow narratif | 22-24 | JEU.5-JEU.16 | Haute |
| JEU.18 | Test avec utilisateur non-voyant | 24-25 | JEU.17 | Critique |
| JEU.19 | Ajustements post-test utilisateur | 25-26 | JEU.18 | Critique |

**Jalons JEU :**
- **SYNC 1 (sem 6) :** Design de la carte complet. Liste des sons établie. Sourcing en cours.
- **SYNC 2 (sem 14) :** Salon + Cuisine + Chambre jouables sur PC avec audio spatial. Navigation inter-pièces fonctionnelle.
- **SYNC 3 (sem 22) :** Toutes les pièces fonctionnelles. Mini-jeux d'exemple prêts. Prêt pour tests utilisateur.

---

### 12.7 Points de synchronisation détaillés

#### SYNC 1 — Semaine 6 : Validation des fondations

**Réunion toutes équipes. Critères de passage :**

| Équipe | Livrable attendu | Validation |
|--------|------------------|------------|
| ELEC | Breadboards fonctionnels (I2S, moteurs, joysticks). Schéma en cours. | Démonstration breadboard |
| ENG | GamepadMapper + stubs + DebugMapper. Début scènes/collisions. | Démo : déplacement au joystick USB avec logs |
| AUD | Prototype HRTF PC 1 source. | Écoute au casque : son qui tourne autour de la tête |
| JEU | Carte de la maison finalisée. Liste des sons. | Document de design validé |

**Décisions à prendre :**
- Valider/ajuster les contrats d'interface si problèmes détectés
- Confirmer la liste de composants pour commande PCB

#### SYNC 2 — Semaine 14 : Prototype logiciel complet sur PC

**Réunion toutes équipes. Critères de passage :**

| Équipe | Livrable attendu | Validation |
|--------|------------------|------------|
| ELEC | PCB fabriqué, soudé, testé électriquement. | PCB boot ESP-IDF |
| ENG | Scènes + collisions + bâton + audio intégrés. | Démo : navigation dans le Salon avec son spatial au casque |
| AUD | PCAudio complet (4-6 sources). Benchmark ESP32 en cours. **Décision software/DSP.** | Rapport benchmark + recommandation |
| JEU | Salon + Cuisine + Chambre jouables. Navigation inter-pièces. | Démo jouable au casque |

**Décisions à prendre :**
- **Go/No-go** sur l'approche audio (software pur vs DSP externe)
- Ajuster le budget si DSP externe nécessaire
- Priorisation des pièces restantes

#### SYNC 3 — Semaine 22 : Intégration matérielle

**Réunion toutes équipes. Critères de passage :**

| Équipe | Livrable attendu | Validation |
|--------|------------------|------------|
| ELEC | Manette complète assemblée (PCB + boîtier + batterie). | Manette physique fonctionnelle |
| ENG | NathanMapper + NathanHaptic + ESP32Audio intégrés. | Jeu tourne sur manette réelle |
| AUD | ESP32Audio fonctionnel et optimisé. | Audio spatial correct sur casque depuis la manette |
| JEU | Toutes pièces + mini-jeux d'exemple. | Jeu complet jouable |

**Décisions à prendre :**
- Go/No-go pour tests utilisateur
- Liste de bugs critiques à corriger

---

### 12.8 Graphe de dépendances critique

```
Phase 0 (toutes) ─┬─→ ELEC.1-4 (breadboard) ─→ ELEC.5 (schéma) ─→ ELEC.6-7 (PCB) ─→ ELEC.9-10 (soudure)
                   │
                   ├─→ ENG.1 (GamepadMapper) ─→ ENG.9 (déplacement) ─→ ENG.10 (bâton) ──┐
                   │                                                                       │
                   ├─→ ENG.2 (StubAudio) ─→ ENG.6 (scènes) ─→ ENG.12 (pont audio) ───────┤
                   │                                                                       │
                   ├─→ AUD.1-3 (recherche+proto) ─→ AUD.5 (PCAudio) ─┬─→ ENG.13 ─────────┤
                   │                                                   │                   │
                   │                                                   └─→ AUD.7 (bench)   │
                   │                                                       ─→ AUD.9 (ESP32)│
                   │                                                                       │
                   └─→ JEU.1-2 (design) ─→ JEU.3 (sons) ─→ JEU.5 (salon) ───────────────┘
                                                                                    │
                                                                                    ▼
                                                            SYNC 2 (sem 14) : tout converge
                                                                                    │
                                                                    ┌───────────────┤
                                                                    ▼               ▼
                                                            ENG.18-20         JEU.12-14
                                                           (NathanMapper)    (école+minijeux)
                                                                    │               │
                                                                    └───────┬───────┘
                                                                            ▼
                                                                    SYNC 3 (sem 22)
                                                                            │
                                                                            ▼
                                                                    JEU.18-19 (tests DV)
```

**Chemin critique :** `P0 → AUD.1 → AUD.3 → AUD.5 → AUD.7 → AUD.8 (décision) → AUD.9 → ENG.20 → ENG.21`

Le **goulot d'étranglement** du projet est le **portage audio HRTF sur ESP32-S3**. C'est pourquoi l'équipe AUD commence dès le jour 1 et que la décision software/DSP est prévue à la semaine 14.

---

### 12.9 Points de référence avec le code existant (GlassBreaker)

| Élément v2.0 | Référence dans GlassBreaker | Notes |
|---|---|---|
| InputMapper | `input/buttons.py` (ButtonManager) | Même pattern, étendre avec joysticks |
| SpatialAudioEngine | `output/audio.py` (AudioManager) | Logique de gestion WAV réutilisable |
| HapticEngine | `output/motors.py` (MotorManager) | Passer de 2 à 5 moteurs avec intensité |
| StorageProvider | `utils/memory.py` (MemoryManager) | Même principe, FAT32 sur SD |
| MiniGameRunner | `game/menu.py` (MenuExtension) | Même pattern classe + `run()` |
| Dossier sons | `/sd/sounds/` | Reproduire en `/sd/minigames/<jeu>/sounds/` |

---

## 13. Budget

### 13.1 Contrainte budgétaire

Budget total : **~500$ CAD** (couvrant prototype + développement)
Objectif de coût de production unitaire : **< 100$ CAD** pour rendre la console accessible

### 13.2 Estimation des coûts hardware prototype

| Composant | Quantité | Coût estimé (CAD) |
|-----------|----------|-------------------|
| ESP32-S3 DevKit (prototype) | 2 | ~30$ |
| PCM5102A (DAC module) | 2 | ~15$ |
| Moteurs vibration ERM 3V | 10 | ~25$ |
| Joysticks analogiques (type PS2) | 4 | ~20$ |
| Batterie LiPo 2500 mAh | 2 | ~30$ |
| Circuit charge TP4056 | 5 | ~10$ |
| Composants divers (résistances, MOSFET, etc.) | — | ~30$ |
| PCB fabrication (JLCPCB, 5 exemplaires) | — | ~40$ |
| Impression 3D filament | — | ~30$ |
| **Manettes USB de substitution (DualShock/Xbox)** | **2-3** | **~60$** |
| Casque stéréo (test) | 1 | ~30$ |
| Câbles, connecteurs, SD card | — | ~20$ |
| **Total prototype** | | **~340$ CAD** |
| **Réserve (imprévus 30%)** | | **~100$ CAD** |
| **Total estimé** | | **~440$ CAD** |

### 13.3 Budget logiciel

- ESP-IDF : **Gratuit** (open-source)
- MicroPython : **Gratuit** (MIT License)
- KiCAD : **Gratuit**
- MIT KEMAR HRTF dataset : **Gratuit** (usage libre)
- Samples audio : **Gratuit** (sources libres de droits — Freesound.org, etc.)
- miniaudio (dev PC) : **Gratuit** (MIT License)

---

## 14. Livrables

### 14.1 Livrables hardware (ELEC)

- [ ] Schéma KiCAD v2.0 complet (ESP32-S3)
- [ ] PCB KiCAD v2.0 (Gerbers prêts)
- [ ] Modèles SolidWorks boîtier v2.0
- [ ] Fichiers STL v2.0 pour impression 3D
- [ ] BOM v2.0 mise à jour
- [ ] Instructions d'assemblage

### 14.2 Livrables firmware et engine (ENG)

- [ ] Contrats d'interface (fichiers `.h` validés)
- [ ] InputMapper : GamepadMapper + DebugMapper + NathanMapper
- [ ] HapticEngine : StubHaptic + GamepadHaptic + NathanHaptic
- [ ] Game engine complet (scènes, collisions, bâton, navigation)
- [ ] Intégration MicroPython + module `nathan`
- [ ] USB CDC protocole pour IDE Cantante
- [ ] Firmware compilé + instructions de flash

### 14.3 Livrables audio (AUD)

- [ ] Rapport de recherche HRTF (choix dataset, taille filtre, performances)
- [ ] PCAudio : implémentation de test sur PC
- [ ] ESP32Audio : implémentation embarquée finale
- [ ] Rapport benchmark ESP32-S3 (CPU, latence, nb sources max)
- [ ] Rapport décision software vs DSP

### 14.4 Livrables jeu (JEU)

- [ ] Premier jeu "La Maison de Nathan" complet (6 zones)
- [ ] Banque de sons (samples + musiques d'ambiance)
- [ ] Narration audio (voix Nathan, tutoriel)
- [ ] 2-3 mini-jeux d'exemple en MicroPython
- [ ] Document de game design (carte, mécaniques, flow)

### 14.5 Livrables documentation (TOUTES)

- [ ] Ce cahier des charges (maintenu à jour)
- [ ] README mis à jour pour v2.0
- [ ] Documentation API game engine
- [ ] Documentation API MicroPython (`nathan.*`)
- [ ] Protocole USB CDC (pour l'intégration Cantante)
- [ ] Guide de contribution open-source

---

*Document vivant — à mettre à jour à chaque jalon atteint.*
*NATHAN Console — Open-source, accessible, pour tous.*
