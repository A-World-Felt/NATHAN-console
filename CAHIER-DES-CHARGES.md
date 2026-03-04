# Cahier des Charges — Projet NATHAN Console (v2.0)

**Projet :** NATHAN — Narrative Audio Terminal for Humans with Alternative Navigation
**Version du document :** 1.1
**Date :** 2026-03-02
**Auteur :** Arthur Olivier Fortin
**Statut :** Phase de conception majeure

---

## Table des matières

1. [Contexte et vision du projet](#1-contexte-et-vision-du-projet)
2. [État actuel du projet (v1.0)](#2-état-actuel-du-projet-v10) — *inclut jeu existant GlassBreaker et IDE Cantante*
3. [Objectifs du projet majeur (v2.0)](#3-objectifs-du-projet-majeur-v20)
4. [Public cible](#4-public-cible)
5. [Spécifications hardware (v2.0)](#5-spécifications-hardware-v20)
6. [Spécifications firmware et logiciel bas niveau](#6-spécifications-firmware-et-logiciel-bas-niveau)
7. [Spécifications du game engine](#7-spécifications-du-game-engine)
8. [Spécifications du premier jeu — La Maison de Nathan](#8-spécifications-du-premier-jeu--la-maison-de-nathan)
9. [Système de mini-jeux et IDE](#9-système-de-mini-jeux-et-ide)
10. [Contraintes et risques techniques](#10-contraintes-et-risques-techniques)
11. [Planification et dépendances](#11-planification-et-dépendances)
12. [Budget](#12-budget)
13. [Livrables](#13-livrables)

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

Cantante est l'application desktop qui servira d'IDE pour programmer les mini-jeux. Elle est en développement actif et sera intégrée dans ce repo.

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
Permettre aux utilisateurs de programmer et jouer à des mini-jeux écrits en **MicroPython** via une interface graphique desktop (Electron/React).

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

## 5. Spécifications hardware (v2.0)

### 5.1 Microcontrôleur — ESP32-S3

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

**Risque :** L'ESP32-S3 standalone pour le rendu HRTF temps réel est exigeant. Voir section 10.

### 5.2 Système audio

#### DAC audio

| Paramètre | Valeur |
|-----------|--------|
| Puce DAC | PCM5102A (Texas Instruments) |
| Interface | I2S |
| Résolution | 32 bits / 384 kHz max |
| SNR | 112 dB |
| Sortie | Jack stéréo 3.5mm (casque uniquement) |
| Amplificateur | Intégré dans PCM5102A (ligne) |

**Note importante :** Le jeu est conçu pour une écoute au **casque stéréo uniquement**. Le son spatial binaural (HRTF) requiert un casque pour l'effet 3D. Un haut-parleur ne peut pas restituer l'effet binaural.

#### Pipeline audio spatial

```
Positions 3D des sons (C++)
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

### 5.3 Système haptique — 5 moteurs en arc

#### Topologie

Les 5 moteurs vibrants sont disposés en arc de cercle dans le corps de la manette, avec une gradation de gauche à droite correspondant à une direction dans l'espace :

```
Position physique :  [M1]  [M2]  [M3]  [M4]  [M5]
Direction simulée :  ←←   ←     ↑     →     →→
```

Ce mapping permet de simuler la direction dans laquelle le bâton d'aveugle entre en contact avec un obstacle.

#### Spécifications moteurs

| Paramètre | Valeur |
|-----------|--------|
| Type | Moteur à vibration excentrique (ERM) ou LRA |
| Tension nominale | 3V |
| Contrôle | PWM individuel par canal (intensité variable) |
| Driver | MOSFET N-CH par moteur (ex: 2N7002) OU DRV2605L (recommandé) |
| Fréquence PWM | 1 kHz minimum |

**Recommandation :** Utiliser le **DRV2605L** (I2C, jusqu'à 8 effets haptics en RAM) pour au moins les moteurs les plus utilisés (bâton), pour la richesse des effets et la réduction du câblage.

#### Cas d'usage

| Interaction | Moteurs activés | Pattern |
|-------------|-----------------|---------|
| Bâton touche mur à gauche | M1, M2 | Impulsion courte, forte |
| Bâton touche sol | M1 à M5 (tous, faible) | Vibration continue faible |
| Bâton touche obstacle à droite | M4, M5 | Impulsion courte, forte |
| Coup de bâton en combat | M1 à M5 (séquence) | Sweep directionnel |
| Guitare — strumming | M3, M4 | Vibration rhythmique |
| Drum — impact | M correspondant à la zone | Impulsion forte courte |

### 5.4 Entrées utilisateur

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
| L2 | À définir | Gâchette analogique gauche (optionnel) |
| R2 | À définir | Gâchette analogique droite (optionnel) |
| Start | Bouton tactile | Menu / pause |
| Select | Bouton tactile | Retour / annuler |

**Note :** Les boutons arcade 30mm doivent être distinguishables au toucher (forme ou position). Envisager différentes textures de capuchon.

#### Potentiomètre (conservé de v1.0)

Réaffecté selon les besoins du jeu (volume ? vitesse ? paramètre contextuel).

### 5.5 Alimentation

| Paramètre | Valeur |
|-----------|--------|
| Batterie | LiPo 1S (3.7V) — capacité min. 2000 mAh |
| Connecteur de charge | USB-C |
| Circuit de charge | TP4056 ou MCP73831 |
| Protection | Surcharge, décharge profonde, court-circuit |
| Régulateur | LDO 3.3V (ex: AMS1117-3.3) pour ESP32-S3 |
| Régulateur 5V | Boost converter si nécessaire pour périphériques 5V |
| Autonomie cible | ≥ 8 heures |

**Note :** Vérifier la consommation totale estimée :
- ESP32-S3 actif : ~240 mA max
- PCM5102A : ~10 mA
- 5 moteurs (simultané max) : ~5 × 150 mA = 750 mA
- Total pic : ~1A → batterie 2000 mAh ≈ 2h en pic, ~6-8h en usage normal

### 5.6 Connectivité

| Interface | Usage |
|-----------|-------|
| USB-C | Charge + connexion à l'IDE mini-jeux (USB CDC/HID) |
| Wi-Fi 2.4 GHz | Mise à jour OTA, téléchargement de mini-jeux (optionnel v2.0) |
| Bluetooth 5.0 | Connexion sans fil à un PC/téléphone (optionnel futur) |
| Micro SD | Stockage assets audio, jeux, mini-jeux |

### 5.7 Boîtier (refonte ergonomique)

#### Contraintes de refonte

- Intégrer 2 joysticks (gauche + droite) — le boîtier v1.0 n'en avait aucun
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

## 6. Spécifications firmware et logiciel bas niveau

### 6.1 Environnement de développement

| Paramètre | Valeur |
|-----------|--------|
| SDK | ESP-IDF v5.x (officiel Espressif) |
| Langage principal | C / C++17 |
| Build system | CMake |
| IDE recommandé | VSCode + extension ESP-IDF |
| Débogage | JTAG via USB (ESP32-S3 supporte le JTAG USB natif) |
| Tests | Unity test framework (embarqué) |

### 6.2 Architecture firmware

```
┌─────────────────────────────────────────────────────────┐
│                      APPLICATION                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Game Engine │  │ MicroPython  │  │   IDE Bridge   │  │
│  │   (C/C++)   │  │  Sandbox     │  │  (USB CDC)     │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         └────────────────┴──────────────────┘            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Hardware Abstraction Layer (HAL)        │ │
│  │  Audio | Haptic | Input | Storage | Power           │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │ ESP-IDF  │ │FreeRTOS│ │  I2S   │ │  SPI   │          │
│  └──────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Tâches FreeRTOS

| Tâche | Priorité | Core | Rôle |
|-------|----------|------|------|
| `task_audio_render` | Très haute | Core 0 | Rendu HRTF + DMA I2S |
| `task_game_logic` | Haute | Core 1 | Logique de jeu, état |
| `task_input_poll` | Haute | Core 1 | Lecture joysticks/boutons à 100 Hz |
| `task_haptic_ctrl` | Moyenne | Core 1 | Contrôle moteurs vibration |
| `task_usb_bridge` | Basse | Core 1 | Communication USB avec IDE |
| `task_sd_io` | Basse | Core 0 | Lecture assets depuis SD |

### 6.4 HAL — Modules à développer

#### Module Audio (`hal_audio`)
- Initialisation I2S + PCM5102A
- Buffer circulaire DMA (double buffer)
- API : `audio_play_sample(id, x, y, z)`, `audio_play_ambient(id)`, `audio_stop(id)`

#### Module Haptique (`hal_haptic`)
- Contrôle PWM des 5 moteurs
- API : `haptic_pulse(motor_id, intensity, duration_ms)`, `haptic_sweep(direction, intensity)`
- Patterns prédéfinis : `HAPTIC_CANE_WALL`, `HAPTIC_CANE_FLOOR`, `HAPTIC_CANE_SWEEP`, etc.

#### Module Entrées (`hal_input`)
- Lecture ADC joysticks (avec anti-rebond et zone morte configurable)
- Lecture GPIO boutons (avec debounce 10 ms)
- API : `input_get_joystick(id, &x, &y)`, `input_get_button(id)`, `input_register_callback(event, cb)`

#### Module Stockage (`hal_storage`)
- Interface SPI avec module micro SD
- Système de fichiers FAT32 via ESP-IDF `sdmmc` driver
- API : `storage_load_sample(path, &buffer)`, `storage_list_minigames()`

### 6.5 Support MicroPython embarqué

Le firmware intègre un interpréteur **MicroPython** via la bibliothèque `micropython-embed` compilée en tant que composant ESP-IDF.

**Note de continuité :** Le jeu existant GlassBreaker tourne en CircuitPython sur Pico. MicroPython et CircuitPython partagent la même syntaxe Python et des APIs très proches — les utilisateurs familiers de l'un peuvent écrire pour l'autre avec peu d'adaptation. Le passage à MicroPython pour v2.0 est donc transparent pour les mini-jeux.

- Les mini-jeux sont des fichiers `.py` sur la carte SD (dossier `/sd/minigames/`)
- L'interpréteur est lancé dans un contexte sandboxé avec accès limité aux APIs HAL
- Un module C expose l'API du moteur à MicroPython :
  - `nathan.audio.play(sound_id, x, y, z)`
  - `nathan.haptic.pulse(motor, intensity)`
  - `nathan.input.read_joystick(id)` → `(x, y)`
  - `nathan.input.read_button(id)` → `bool`
- Les sons des mini-jeux sont stockés dans `/sd/minigames/<nom_jeu>/sounds/` (même convention que GlassBreaker : `sounds/` sur SD)

---

## 7. Spécifications du game engine

### 7.1 Philosophie du moteur

Le moteur est conçu pour un jeu **entièrement auditif**. Il n'y a pas de rendu graphique. Le "monde" est une grille 2D avec une coordonnée de hauteur. Les sons sont les seuls retours d'état du monde.

### 7.2 Représentation du monde

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

#### Calcul HRTF

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

### 7.3 API du game engine

```cpp
// Gestion de scène
Scene* scene_create(const char* name);
void scene_load(Scene* s);
void scene_unload(Scene* s);

// Entités sonores
SoundEntity* entity_create(float x, float y, float z, const char* sound_file);
void entity_set_position(SoundEntity* e, float x, float y, float z);
void entity_set_looping(SoundEntity* e, bool loop);
void entity_play(SoundEntity* e);
void entity_stop(SoundEntity* e);

// Joueur
void player_set_position(float x, float y);
void player_set_orientation(float angle_deg);
void player_move(float dx, float dy); // déplacement relatif

// Collisions (murs/obstacles)
void world_add_wall(float x1, float y1, float x2, float y2);
bool world_check_collision(float x, float y, float radius);

// Audio ambiant (non spatial)
void ambient_play(const char* sound_file, float volume);
void ambient_stop();

// Haptique depuis le moteur
void engine_haptic_cane(float contact_x, float contact_y); // déclenche pattern arc
```

### 7.4 Système de collisions et bâton

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

## 8. Spécifications du premier jeu — La Maison de Nathan

### 8.1 Concept général

**Titre :** La Maison de Nathan (ou simplement "NATHAN")
**Genre :** Jeu de vie / exploration sensorielle
**Perspective :** Première personne sonore (FPS audio)
**Durée :** Jeu ouvert (pas de fin définie — exploration libre + quêtes)

Le joueur incarne **Nathan**, un adolescent aveugle. Il doit accomplir des tâches quotidiennes, explorer sa maison, jouer de la musique, aller à l'école, et affronter des adversaires imaginaires avec son bâton.

### 8.2 Structure de la maison

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │
│  │  CUISINE │  │  SALON   │  │    CHAMBRE     │    │
│  │  🍳      │  │  (HUB)   │  │    🛏️          │    │
│  └──────────┘  └────┬─────┘  └────────────────┘    │
│                     │                               │
│  ┌──────────┐  ┌────┴─────┐  ┌────────────────┐    │
│  │ SALLE DE │  │          │  │  SALLE DE      │    │
│  │ MUSIQUE  │  │ COULOIR  │  │  MINI-JEUX     │    │
│  │ 🎸 🥁    │  │          │  │  💻            │    │
│  └──────────┘  └────┬─────┘  └────────────────┘    │
│                     │                               │
│             ┌───────┴──────┐                        │
│             │    ÉCOLE     │                        │
│             │  (extérieur) │                        │
│             └──────────────┘                        │
└─────────────────────────────────────────────────────┘
```

### 8.3 Pièce 1 — Le Salon (Hub principal)

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

### 8.4 Pièce 2 — La Cuisine

**Audio :** Musique rythmée type jazz. Sons de cuisine (réfrigérateur, eau, vaisselle).

**Mini-jeu principal : Faire à manger**
- Objectif : Suivre une recette audio étape par étape
- Mécanique : Les joysticks imitent des gestes culinaires (mélanger = rotation joystick gauche, couper = up/down joystick droit)
- Feedback haptique : résistance simulée selon la texture des aliments
- Succès/échec évalué par la précision du geste et le timing

**Éléments interactifs :**
- Réfrigérateur (inventaire d'ingrédients, son caractéristique)
- Casserole (sons de cuisson évolutifs selon la cuisson)
- Robinet (son de l'eau)

### 8.5 Pièce 3 — La Chambre

**Audio :** Musique calme / ASMR. Sons de chambre (ventilateur, pluie sur la fenêtre, horloge).

**Mini-jeux :**
- **Se lever le matin :** réveil, s'habiller (séquence de boutons au son)
- **Exploration libre :** Fouiller les tiroirs, découvrir des souvenirs audio (voix de proches, musiques du passé)

**Éléments interactifs :**
- Lit (point de sauvegarde)
- Radio (change la musique d'ambiance)
- Bureau (accès aux devoirs — mini-jeu de mémorisation sonore)

### 8.6 Pièce 4 — La Salle de Musique

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
**Feedback haptique :** Vibration légère des moteurs à chaque strum (simuler la vibration des cordes).

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
**Feedback haptique :** Impact fort et court sur le/les moteurs correspondant à la position du coup.

**Mode enregistrement :** Possibilité d'enregistrer une séquence et de la rejouer (sequencer simple).

### 8.7 Pièce 5 — La Salle de Mini-Jeux

**Audio :** Musique arcade 8-bit. Sons d'ordinateur/console.

**Gameplay :**
- Hub des mini-jeux créés par l'utilisateur via l'IDE
- Nathan s'assoit à son poste et peut lancer un mini-jeu de la liste disponible sur la carte SD
- Navigation dans la liste des mini-jeux par audio (lecture du nom du fichier ou métadonnée "titre")
- Retour au salon après fin d'un mini-jeu

### 8.8 Zone 6 — L'École (extérieur)

**Audio :** Sons de rue, bruits urbains, cour d'école, voix des camarades.

**Mécanique principale : Navigation avec le bâton**

C'est ici que le bâton d'aveugle est le contrôle primaire :
- **Joystick droit** : contrôle la direction du bâton (360°)
- Le raycast détecte obstacles, bordures de trottoir, portes
- Les **5 moteurs** donnent la direction du contact
- Le **son** de frappe change selon la surface (sol : tap doux / bois ; mur : bruit sourd)

**Sous-zones de l'école :**
- Trajet aller (navigation en rue — obstacles mobiles : piétons)
- Cour de récréation (interactions sociales audio avec personnages)
- Salle de classe (mini-jeux pédagogiques : maths, mémoire, musique)

**Combats imaginaires :**
- Déclenchés optionnellement dans certaines zones
- Le bâton devient arme : mêmes contrôles, adversaires signalés par sons directionnels
- Détection de coup : le raycast touche un ennemi → impact fort + son d'impact
- L'ennemi riposte → vibration directionnelle + son d'attaque (le joueur peut parer)

### 8.9 Contrôles de déplacement global

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

### 8.10 Système de navigation sonore inter-pièces

Chaque pièce émet une **signature musicale** différente. Depuis le couloir, les musiques des pièces adjacentes sont audibles en spatialisation. Plus le joueur approche d'une porte, plus la musique de la pièce correspondante est forte et plus son positionnement directionnel est précis. Cela permet une navigation intuitive sans aucun repère visuel.

---

## 9. Système de mini-jeux et IDE

### 9.1 Architecture générale

```
┌─────────────────────┐         ┌─────────────────────────┐
│     PC / Mac        │  USB-C  │      ESP32-S3           │
│                     │◄───────►│                         │
│  IDE Electron/React │         │  MicroPython Sandbox    │
│  ┌───────────────┐  │         │  ┌──────────────────┐   │
│  │ Éditeur code  │  │         │  │  mini_game.py    │   │
│  │ Visualisateur │  │         │  │                  │   │
│  │ de scène 2D   │  │         │  │  nathan.audio    │   │
│  │ Simulateur    │  │         │  │  nathan.haptic   │   │
│  │ audio virtuel │  │         │  │  nathan.input    │   │
│  └───────────────┘  │         │  └──────────────────┘   │
└─────────────────────┘         └─────────────────────────┘
```

### 9.2 IDE — Cantante : état actuel et fonctionnalités à ajouter

L'IDE est **Cantante**, une application **Electron 28 + React 18 + TypeScript** déjà existante (`C:\Cantante`), à intégrer dans ce dépôt sous `ide/`.

**Fondation déjà disponible dans Cantante :**
- Éditeur de code multi-onglets avec syntaxe highlighting
- Explorateur de fichiers complet
- Terminal intégré (exécution shell avec streaming)
- Accessibilité vocale complète (TTS français par défaut)
- Maestro backend (C# .NET) pour assistance IA — peut être utilisé pour expliquer les erreurs de code aux utilisateurs DV

#### Fonctionnalités à ajouter dans Cantante pour NATHAN

##### Éditeur MicroPython
- Remplacer/étendre le tokenizer de syntaxe pour MicroPython (mots-clés `def`, `class`, `import`, types, etc.)
- Auto-complétion de l'API `nathan.*` (studio Monaco Editor ou solution légère custom)
- Validation syntaxique Python basique (détection d'erreurs d'indentation)

##### Éditeur de scène 2D
- Grille 2D interactive (canvas React ou SVG)
- Drag & drop de sources sonores avec paramètre X, Y, Z
- Aperçu visuel des murs/obstacles
- Simulation audio WebAudio API avec HRTF simplifié (aperçu sur PC avant envoi)

##### Communication USB avec la console
- Détection automatique de la console NATHAN connectée (USB CDC via Web Serial API ou lib `serialport`)
- Upload d'un mini-jeu (`.py` + dossier `sounds/`) vers carte SD via USB
- Lecture de la liste des mini-jeux présents sur la carte SD
- Affichage des logs/erreurs de la console en temps réel

##### Gestionnaire de mini-jeux
- Liste des `.py` sur la carte SD connectée
- Upload / suppression / renommage
- Lecture et affichage des métadonnées `META = { "title", "author", "description" }`
- Lecture audio du titre et de la description (accessibilité)

### 9.3 API MicroPython exposée aux mini-jeux

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
# Retourne True si appuyé ce frame

# Contrôle du jeu
nathan.game.score(points: int)
nathan.game.end(success: bool)
nathan.game.set_title(title: str)

# Utilitaires
nathan.sleep_ms(ms: int)  # attente non bloquante
nathan.time_ms() -> int   # temps depuis démarrage
```

### 9.4 Format de mini-jeu

Le format est **directement inspiré** de l'architecture GlassBreaker existante (`game/logic.py`, `game/menu.py`). Un mini-jeu est une **classe Python** avec métadonnées et méthodes standardisées.

```python
# Structure d'un mini-jeu NATHAN (MicroPython)
# Inspiré du pattern MenuExtension de GlassBreaker (NATHAN-code/game/menu.py)

import nathan

META = {
    "title": "Mon Mini-Jeu",          # Lu à voix haute dans le hub
    "author": "Arthur",
    "description": "Un jeu de mémoire sonore"  # Annoncé avant démarrage
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
        Retourne True pour continuer, False pour terminer le mini-jeu.
        """
        x, y = nathan.input.joystick(0)
        if nathan.input.button(0):   # Bouton A
            nathan.audio.play("confirm.wav", 0, 0, 0)
            nathan.haptic.pulse(2, 0.8, 100)  # moteur central
            self.score += 1
        # Fin du jeu si score atteint
        if self.score >= 10:
            nathan.game.end(success=True)
            return False
        return True

# Point d'entrée appelé par le game engine
def create():
    return MonMiniJeu()
```

**Structure de fichiers sur la carte SD pour un mini-jeu :**
```
/sd/minigames/
└── mon_mini_jeu/
    ├── main.py          # Fichier principal (contient META + classe)
    └── sounds/          # Sons du mini-jeu (WAV 16 bits, 44.1kHz, mono)
        ├── intro.wav
        ├── confirm.wav
        └── arcade_ambient.wav
```

> **Référence directe :** Cette structure est analogue à GlassBreaker où chaque mode de jeu est une entrée du `MenuSystem` avec ses propres sons dans `/sd/sounds/`. La différence principale est que les mini-jeux v2.0 sont des fichiers externes chargés dynamiquement, au lieu d'être compilés dans le firmware.

---

## 10. Contraintes et risques techniques

### 10.1 Risques majeurs

#### Risque R1 — HRTF temps réel sur ESP32-S3 (CRITIQUE)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Critique |
| Description | Le rendu HRTF temps réel (convolution) est très coûteux en CPU. Avec plusieurs sources sonores simultanées, l'ESP32-S3 pourrait atteindre ses limites. |
| Impact | Latence audio, artifacts, ou limitation du nombre de sons simultanés |
| Mitigation 1 | Utiliser des HRTF avec réponses impulsionnelles courtes (128 samples au lieu de 512) |
| Mitigation 2 | Limiter à 4-6 sources sonores spatiales simultanées |
| Mitigation 3 | Pré-calculer les positions pour les sons statiques (bake offline) |
| Mitigation 4 | En fallback, audio stéréo simple (panoramique L/R) sans HRTF si charge trop haute |

#### Risque R2 — Autonomie batterie (ÉLEVÉ)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Élevé |
| Description | 5 moteurs + ESP32-S3 actif + DAC = consommation pic ~1A |
| Mitigation | Gérer l'activation des moteurs (jamais tous 5 en continu), sleep du Wi-Fi quand inutile, 2500 mAh minimum |

#### Risque R3 — MicroPython sur ESP32-S3 (MOYEN)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Moyen |
| Description | L'intégration de MicroPython comme composant ESP-IDF en parallèle du game engine C++ est complexe |
| Mitigation | Utiliser `micropython-embed`, dédier le Core 0 au game engine et le Core 1 à l'interpréteur MicroPython |

#### Risque R4 — Ergonomie boîtier avec 2 joysticks (MOYEN)

| Paramètre | Détail |
|-----------|--------|
| Niveau | Moyen |
| Description | La refonte mécanique est importante. Le boîtier v1.0 ne supporte pas 2 joysticks. |
| Mitigation | Prototype en impression 3D rapide, validation ergonomique avant fabrication finale |

### 10.2 Contraintes techniques reconnues

- ESP32-S3 : RAM totale 8 MB PSRAM — les HRTF lookup tables MIT KEMAR prennent ~1 MB, laisser ~6 MB pour le moteur et les samples audio en buffer
- Micro SD : Latence de lecture (~few ms) — les samples audio doivent être pré-chargés en RAM avant lecture
- MicroPython : Vitesse d'exécution ~10-50x plus lente que C — les mini-jeux sont des jeux simples, pas de physique complexe
- PCM5102A : Pas de contrôle de volume hardware — le volume doit être géré par software (atténuation dans le buffer audio)

---

## 11. Planification et dépendances

### 11.1 Vue d'ensemble des phases

```
Phase 1 : Refonte Hardware          ████████░░░░░░░░░░░░░░░░░░░░░░░░
Phase 2 : Firmware de base          ░░░░████████░░░░░░░░░░░░░░░░░░░░
Phase 3 : Game Engine               ░░░░░░░░████████░░░░░░░░░░░░░░░░
Phase 4 : Premier jeu               ░░░░░░░░░░░░████████████░░░░░░░░
Phase 5 : Système mini-jeux         ░░░░░░░░░░░░░░░░████████████░░░░
Phase 6 : IDE Electron/React        ░░░░████████████████░░░░░░░░░░░░
Phase 7 : Intégration & tests       ░░░░░░░░░░░░░░░░░░░░████████░░░░
```

---

### 11.2 Phase 1 — Refonte Hardware

**Durée estimée :** 6-10 semaines
**Prérequis :** Aucun

#### Tâches

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| H1 | Sélection et commande ESP32-S3 DevKit | — | Critique |
| H2 | Breadboard prototype ESP32-S3 + PCM5102A + test I2S | H1 | Critique |
| H3 | Breadboard prototype 5 moteurs + PWM | H1 | Haute |
| H4 | Breadboard prototype 2 joysticks ADC | H1 | Haute |
| H5 | Schéma KiCAD v2.0 complet | H2, H3, H4 | Critique |
| H6 | PCB KiCAD v2.0 layout | H5 | Critique |
| H7 | Commande PCB (JLCPCB / PCBWay) | H6 | Critique |
| H8 | Soudure et tests PCB v2.0 | H7 | Critique |
| H9 | Refonte boîtier SolidWorks v2.0 | H4, H3 | Haute |
| H10 | Impression 3D prototype boîtier | H9 | Haute |
| H11 | Test ergonomie boîtier | H10 | Moyenne |
| H12 | Mise à jour BOM v2.0 | H5 | Moyenne |

**Jalon Phase 1 :** Prototype hardware fonctionnel (ESP32-S3 + audio + haptique + contrôles)

---

### 11.3 Phase 2 — Firmware de base (HAL)

**Durée estimée :** 4-6 semaines
**Prérequis :** H2, H3, H4 (breadboard au minimum)

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| F1 | Setup projet ESP-IDF, structure CMake | H1 | Critique |
| F2 | `hal_audio` : Init I2S + PCM5102A, lecture WAV depuis SD | F1, H2 | Critique |
| F3 | `hal_input` : Lecture joysticks ADC + boutons GPIO | F1, H4 | Critique |
| F4 | `hal_haptic` : PWM 5 moteurs, patterns de base | F1, H3 | Haute |
| F5 | `hal_storage` : Interface micro SD, FAT32, listing fichiers | F1 | Haute |
| F6 | Gestion alimentation : lecture niveau batterie, sleep | F1 | Moyenne |
| F7 | USB CDC : communication série avec PC (pour IDE) | F1 | Haute |
| F8 | Tests unitaires HAL (Unity framework) | F2-F7 | Haute |

**Jalon Phase 2 :** La console joue un son WAV depuis la SD, les joysticks sont lus, les moteurs vibrent

---

### 11.4 Phase 3 — Game Engine

**Durée estimée :** 6-8 semaines
**Prérequis :** F2, F3, F4, F5

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| E1 | Représentation monde 2D+Z, gestion entités | F1 | Critique |
| E2 | Calcul azimut/élévation/distance par source | E1 | Critique |
| E3 | HRTF lookup tables (MIT KEMAR, intégration binaire) | E2 | Critique |
| E4 | Rendu audio binaural (convolution + mix + DMA) | E2, E3, F2 | Critique |
| E5 | Système de collision (murs, raycast bâton) | E1 | Haute |
| E6 | Gestion scènes (load/unload, transitions) | E1, E4 | Haute |
| E7 | API publique game engine documentée | E1-E6 | Haute |
| E8 | Déplacement joueur + orientation | E1, E5, F3 | Haute |
| E9 | Simulation bâton (raycast + haptique directionnel) | E5, E8, F4 | Haute |
| E10 | Tests moteur (scène de test avec sons positionnés) | E7 | Haute |

**Jalon Phase 3 :** Scène de test : le joueur marche dans un couloir, les sons sont spatialisés correctement, le bâton détecte les murs

---

### 11.5 Phase 4 — Premier jeu : La Maison de Nathan

**Durée estimée :** 10-16 semaines
**Prérequis :** E7, E9

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| G1 | Banque de sons (samples, musiques d'ambiance) | — | Critique |
| G2 | Design de la carte de la maison (coordonnées 2D) | E7 | Critique |
| G3 | Système de navigation inter-pièces (audio signatures) | E6, G2 | Critique |
| G4 | Salon — ambiance et interactions de base | G2, G3 | Haute |
| G5 | Tutoriel intégré (voix Nathan) | G4 | Haute |
| G6 | Cuisine — mini-jeu "faire à manger" | G2, E9 | Haute |
| G7 | Chambre — exploration + point de sauvegarde | G2 | Moyenne |
| G8 | Salle de musique — guitare | G2, F3, F4 | Haute |
| G9 | Salle de musique — batterie | G2, F3, F4 | Haute |
| G10 | Zone école — navigation bâton en extérieur | E9, G2 | Haute |
| G11 | Salle de mini-jeux — hub de lancement | G2, MJ4 | Haute |
| G12 | Système de combats (bâton comme arme) | E9, G10 | Moyenne |
| G13 | Tâches quotidiennes additionnelles | G4, G6, G7 | Basse |
| G14 | Narration audio (voix du personnage) | G1 | Haute |

**Jalon Phase 4 :** Jeu complet jouable avec toutes les pièces et mécaniques de base

---

### 11.6 Phase 5 — Système de mini-jeux

**Durée estimée :** 4-6 semaines
**Prérequis :** F5, F7, E7

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| MJ1 | Intégration MicroPython (micropython-embed + ESP-IDF) | F1 | Critique |
| MJ2 | Module `nathan` Python : bridge C → MicroPython | MJ1, E7, F3, F4 | Critique |
| MJ3 | Loader de mini-jeux depuis SD | MJ1, F5 | Critique |
| MJ4 | Hub in-game (liste de mini-jeux navigable à l'audio) | MJ3, E7 | Haute |
| MJ5 | Sandbox sécurisée (limite temps, mémoire) | MJ1 | Haute |
| MJ6 | 2-3 mini-jeux d'exemple fournis | MJ2 | Haute |
| MJ7 | Documentation API MicroPython | MJ2 | Haute |

**Jalon Phase 5 :** Un mini-jeu `.py` simple peut être joué depuis la console

---

### 11.7 Phase 6 — IDE Cantante (intégration NATHAN)

**Durée estimée :** En cours (parallèle aux phases 2-5)
**Prérequis :** F7 (communication USB firmware) pour les tâches de connexion hardware

> Cantante existe déjà avec une base solide (éditeur, fichiers, terminal, TTS, Maestro IA). Les tâches ci-dessous portent uniquement sur les **ajouts spécifiques à NATHAN**.

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| IDE1 | Intégration de Cantante dans ce repo (`ide/`) | — | Critique |
| IDE2 | Coloration syntaxique MicroPython (étendre tokenizer existant) | IDE1 | Critique |
| IDE3 | Template de mini-jeu (nouveau fichier = structure de base pré-remplie) | IDE1 | Haute |
| IDE4 | Auto-complétion API `nathan.*` | IDE2 | Haute |
| IDE5 | Communication USB CDC (Web Serial API ou `serialport`) | F7 | Critique |
| IDE6 | Upload mini-jeu (`.py` + `sounds/`) vers carte SD via USB | IDE5 | Critique |
| IDE7 | Lecture liste mini-jeux sur carte SD via USB | IDE5 | Haute |
| IDE8 | Gestionnaire de mini-jeux (liste, supprimer, renommer, métadonnées) | IDE7 | Haute |
| IDE9 | Visualisateur de scène 2D (grille drag & drop sources sonores) | IDE1 | Haute |
| IDE10 | Simulation audio WebAudio + HRTF simplifié | IDE9 | Moyenne |
| IDE11 | Affichage logs/erreurs console en temps réel | IDE5 | Haute |
| IDE12 | Mode accessibilité renforcé (grand texte, fort contraste, navigation vocale complète) | IDE1 | Haute |
| IDE13 | Build/package installeur (Windows/Mac/Linux via Electron Builder) | IDE1-IDE12 | Basse |

**Jalon Phase 6 :** L'IDE permet d'écrire un mini-jeu, le tester visuellement, et l'envoyer sur la console en un clic — le tout navigable entièrement au clavier et à la voix

---

### 11.8 Phase 7 — Intégration, polish et tests

**Durée estimée :** 4-6 semaines
**Prérequis :** Toutes phases précédentes

| ID | Tâche | Dépendances | Priorité |
|----|-------|-------------|----------|
| T1 | Tests d'intégration hardware/firmware complets | H8, F8 | Critique |
| T2 | Test utilisateur avec une personne non-voyante | G14 | Critique |
| T3 | Ajustements suite au test utilisateur | T2 | Critique |
| T4 | Optimisation performances audio (profiling) | E4 | Haute |
| T5 | Mise à jour documentation complète | Tout | Haute |
| T6 | Release v2.0 (tag git, binaires) | T3, T4, T5 | Haute |

---

### 11.9 Graphe de dépendances critique

```
H1 → H2 → F2 → E4 → G3 (navigation sonore)
H1 → H3 → F4 → E9 → G12 (combat/bâton)
H1 → H4 → F3 → E8 → G4 (déplacement)
H1 → H4 → F3 → G8/G9 (instruments)
H1 → H5 → H6 → H7 → H8 (PCB final)
F1 → MJ1 → MJ2 → MJ3 → MJ4 → G11 (mini-jeux in-game)
F7 → IDE5 → IDE6 (upload IDE → console)
IDE1 → IDE2 → IDE3 (Cantante, indépendant du hardware)
```

**Chemin critique :** `H1 → H2 → F2 → E3 → E4 → G3`
(Hardware → Audio I2S → HRTF → Navigation sonore)

### 11.10 Points de référence avec le code existant

| Élément v2.0 | Référence dans GlassBreaker | Notes |
|---|---|---|
| HAL audio | `output/audio.py` (AudioManager) | Migrer la logique de gestion des WAV |
| HAL input | `input/buttons.py` (ButtonManager) | Étendre avec joysticks ADC |
| HAL haptique | `output/motors.py` (MotorManager) | Passer de 2 à 5 moteurs avec intensité |
| Persistance scores | `utils/memory.py` (MemoryManager) | Même principe, FAT32 sur SD |
| Format mini-jeu | `game/menu.py` (MenuExtension) | Même pattern classe + `run()` |
| Dossier sons | `/sd/sounds/` | Reproduire en `/sd/minigames/<jeu>/sounds/` |
| Convention WAV | `{1-5}H.wav`, `{1-5}C{mode}.wav` | Définir convention v2.0 similaire |

---

## 12. Budget

### 12.1 Contrainte budgétaire

Budget total : **~500$ CAD** (couvrant prototype + développement)
Objectif de coût de production unitaire : **< 100$ CAD** pour rendre la console accessible

### 12.2 Estimation des coûts hardware prototype

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
| Casque stéréo (test) | 1 | ~30$ |
| Câbles, connecteurs, SD card | — | ~20$ |
| **Total prototype** | | **~280$ CAD** |
| **Réserve (imprévus 30%)** | | **~85$ CAD** |
| **Total estimé** | | **~365$ CAD** |

### 12.3 Budget logiciel

- ESP-IDF : **Gratuit** (open-source)
- MicroPython : **Gratuit** (MIT License)
- KiCAD : **Gratuit**
- MIT KEMAR HRTF dataset : **Gratuit** (usage libre)
- Samples audio : **Gratuit** (sources libres de droits — Freesound.org, etc.)

---

## 13. Livrables

### 13.1 Livrables hardware

- [ ] Schéma KiCAD v2.0 complet (ESP32-S3)
- [ ] PCB KiCAD v2.0 (Gerbers prêts)
- [ ] Modèles SolidWorks boîtier v2.0 (assemblage + pièces)
- [ ] Fichiers STL v2.0 pour impression 3D
- [ ] BOM v2.0 mise à jour
- [ ] Instructions d'assemblage (dossier `Assembly Instructions/`)

### 13.2 Livrables firmware

- [ ] Projet ESP-IDF structuré dans `firmware/`
- [ ] HAL complet (audio, haptique, input, stockage)
- [ ] Game engine C/C++ avec API documentée
- [ ] Intégration MicroPython + module `nathan`
- [ ] Firmware compilé + instructions de flash

### 13.3 Livrables jeu

- [ ] Premier jeu "La Maison de Nathan" complet
- [ ] Banque de sons (samples + musiques d'ambiance)
- [ ] 2-3 mini-jeux d'exemple en MicroPython

### 13.4 Livrables IDE (Cantante intégré)

- [ ] Cantante intégré dans ce repo (`ide/`)
- [ ] Support syntaxique MicroPython
- [ ] Connexion USB + upload mini-jeux
- [ ] Visualisateur de scène 2D
- [ ] Documentation d'utilisation accessible
- [ ] Build installable Windows/Mac/Linux

### 13.5 Livrables documentation

- [ ] Ce cahier des charges (maintenu à jour)
- [ ] README mis à jour pour v2.0
- [ ] Documentation API game engine
- [ ] Documentation API MicroPython (`nathan.*`)
- [ ] Guide de contribution open-source

---

*Document vivant — à mettre à jour à chaque jalon atteint.*
*NATHAN Console — Open-source, accessible, pour tous.*
