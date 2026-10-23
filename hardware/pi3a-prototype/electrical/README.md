# Schémas D1 — connexions proposées pour revue

Auteur : Codex/OpenAI `nathan_bom`. Les projets `controls/nathan-controls.kicad_pro` et `base/nathan-base.kicad_pro` contiennent des schémas KiCad 8 éditables. Les symboles fonctionnels locaux portent des broches numérotées ; leurs connexions sont nommées explicitement. `design-networks.json`, `pin-map.csv` et `bom-proposal.csv` détaillent la source et la limite de chaque proposition.

La carte commandes comprend **93 composants physiques proposés et 4 déclarations ERC**, répartis entre interface, entrées numériques, entrées analogiques, multiplexeur, cinq branches haptiques et buck. Son ERC natif actuel rapporte **0 violation**. L’export natif initial, comparé au modèle broche par broche, ne présentait aucune connexion divergente ou absente. Un ERC réussi ne remplace ni la vérification du dessin fabricant, ni le dimensionnement thermique, ni les essais du matériel.

La porteuse comprend encore **8 interfaces de travail**, et non des circuits USB/audio terminés. Les nets `USB_PC_VBUS`, `USB_CHARGE_LIMITED` et `5V_SYS` restent distincts. Aucun fil artificiel ne remplace les protections et contrôles manquants. Le projet PCB D0.1 est une étude de placement séparée : **ces schémas D1 ne sont pas encore intégralement reportés et routés sur les deux PCB**.

## Choix proposés à partir des données connues

Le lancement ERC reproductible et son contournement de première initialisation KiCad 8.0.2 sont documentés dans [incident-kicad.md](../docs/incident-kicad.md). La comparaison indépendante du checkout de revue couvre 317 broches physiques, sans différence ; son rapport est `validation/native-current/controls-netlist-comparison.json`.

| Choix D1 | Motif et limite |
|---|---|
| MCP3208-CI/SL à la place du MCP3008 | Résolution 12 bits conforme au texte du cahier des charges. Brochage SOIC-16 vérifié ; trames SPI/logiciel à adapter. Ce remplacement n’est pas effectué dans le classeur original. |
| L2/R2 analogiques | Variante cohérente avec les deux potentiomètres envisagés dans le BOM ; elle conserve 14 entrées numériques avec L1/R1 et les clics des sticks. Technologie mécanique/capteur à sélectionner. |
| MCP23017-E/SO, 14 entrées seulement | Les broches GPA7/GPB7 restent inutilisées comme entrées ; configuration en sorties basses prévue. INTA porte l’interruption miroir ; INTB reste libre. |
| TCA9548APWR, adresse 0x70 | Cinq branches pour les cinq DRV2604L à 0x5A ; une branche sélectionnée par transaction. |
| DRV2604LDGSR | Brochage DGS vérifié. REG et VDD découplés, IN/TRIG à la masse, EN au rail haptique ; chaque moteur reste connecté entre les deux sorties différentielles. |
| Logique sur 3V3_PI, moteurs sur buck séparé | Aucun parallélisme entre régulateurs 3,3 V. Les pull-up aval suivent le rail moteur ; séquencement des alimentations encore à vérifier. |
| TPS62080DSGR conservé | Diviseur 249 kΩ/39,2 kΩ : 3,308 V nominal. Inductance 1 µH et condensateurs selon l’application TI, avec qualification des références/dérating encore requise. |
| Nappe GPIO polarisée | La porteuse inférieure ne peut pas être supposée enfichable sous le Pi : le PiSugar occupe cette zone par ses contacts pogo et le GPIO du Pi est dirigé vers le haut. La nappe préserve démontabilité et séparation des supports. |

Les broches 15/16 du connecteur intercartes D1 deviennent `3V3_PI` et `CTRL_RESET_N` ; elles étaient réservées dans D0.1. Ne pas fabriquer ni mélanger une nappe et une carte à partir de révisions différentes. Le fichier historique `pcb/interboard-interface.csv` décrit encore D0 ; le contrat D1 fait foi dans `pin-map.csv`, références J100 des deux cartes.

Le démarrage logiciel doit configurer l’extension, les interruptions, la sélection du multiplexeur et le mode LRA. La consigne VG0832013D reste 1,8 Vrms ; alimenter le driver en 3,3 V ne définit pas sa consigne moteur. SPI à 100 kHz et conversion d’amorçage après changement de voie sont proposés pour qualifier le filtre d’entrée ; aucune précision effective de 12 bits n’est garantie par le seul nombre de bits du composant.

## Sources vérifiées

- [Microchip MCP3208, DS21298E](https://ww1.microchip.com/downloads/en/DeviceDoc/21298e.pdf), tableau 3-1 page 15 et acquisition pages 17–18.
- [Microchip MCP23017, DS20001952D](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf), pages 1 et 11.
- [TI TCA9548A, SCPS207H](https://www.ti.com/lit/ds/symlink/tca9548a.pdf), brochage page 3.
- [TI DRV2604L, SLOS866F](https://www.ti.com/lit/ds/symlink/drv2604l.pdf), DGS page 4.
- [TI TPS62080, SLVSAE8F](https://www.ti.com/lit/ds/symlink/tps62080.pdf), pages 4, 12–14 et 19.

## Ce qu’il reste avant une carte complète

1. Qualifier les connecteurs/câbles et les références passives, terminer les empreintes de l’inductance et des commandes physiques.
2. Réaliser la chaîne casque, sa commande de volume/mute et son alimentation ; PCM5102A seul reste une sortie ligne.
3. Définir le circuit du port commun : courant d’entrée autorisé selon la source, blocage inverse, détection VBUS, protection ESD et raccordement USB périphérique du Pi.
4. Reporter la netlist finale aux PCB, adapter le placement, router puis vérifier chaque carte et sa correspondance au schéma.
5. Valider l’empilement réel et les mouvements dans l’assemblage, puis effectuer les essais électriques/thermiques/USB/autonomie.

Les éléments bloqués sont précisément visibles dans les connecteurs et notes du schéma. Ils ne sont ni masqués par des réserves présentées comme pièces réelles ni remplacés par des pistes arbitraires.
