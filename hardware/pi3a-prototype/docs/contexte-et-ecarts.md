# Contexte technique lu et écarts à réconcilier

Les sources techniques proviennent de NATHAN-console. Les chemins ci-dessous sont relatifs à la racine du dépôt ; les documents sont référencés sans être recopiés intégralement.

| Source | Fait utile | Effet sur la conception |
|---|---|---|
| `CLAUDE.md:2–8` | Dépôt cible `A-World-Felt/NATHAN-console`, branche de travail/publication `main` | La PR appartient à ce projet ; aucune publication dans dev-kit. Le parent gère l’isolation et la publication. |
| `CONTRIBUTING.md`, règle d’or et gabarit | Décision de conception significative → ADR initialement proposé | Une proposition ADR-0008 est fournie ; aucun ADR accepté n’est réécrit. |
| `README.md`, What is NATHAN / Features | Inspiration Xbox ; description historique Pico/cinq boutons | Référence de forme, pas spécification actuelle du calculateur ou du nombre de boutons. |
| `docs/specs/REQUIS.md:70` | R-24 : USB-C, autonomie typique ≥4 h | La demande récente micro-USB constitue un écart à tracer. La cible d’autonomie est désormais connue. |
| `docs/specs/REQUIS.md:72,128`, `CONTRAINTES.md:33`, ADR-0005 | Communication USB CDC ; transfert de fichier vérifié | SSH/SFTP peut servir à la maintenance, mais ne remplace pas implicitement le contrat série de l’IDE. |
| `docs/specs/REQUIS.md:73`, `CONTRAINTES.md:79` | Largeur ≤160 mm | Profil D0 ramené à 160 mm ; confort et préhension non testés. |
| `docs/specs/CAHIER-DES-CHARGES.md:486–504` | Cinq moteurs en arc ; ancien dimensionnement générique 3 V / ERM ou LRA | Les VG0832013D du BOM sont des LRA 1,8 Vrms : conserver leurs limites réelles, pas la tension générique du document. |
| `docs/specs/CAHIER-DES-CHARGES.md:520–525` | ADC annoncé 12 bits | MCP3008 du BOM : 10 bits ; divergence ouverte. |
| `docs/specs/CAHIER-DES-CHARGES.md:562–571` | Refonte FDM, joysticks, arc dans les poignées, inspiration Xbox | Les positions, forme de coque et supports moteurs sont éditables, mais les montages et efforts restent à vérifier. |
| `docs/specs/REQUIS.md:54–58`, ADR-0003 | Performances et sélection quantitative de calculateur | Le Pi 3 A+ confirmé ne vaut pas benchmark ni conformité aux latences/boot. |
| `docs/specs/CONTRAINTES.md:43` et `BOM!I33` du classeur reçu | Cibles de coût documentaire et du classeur différentes | Périmètre et version à réconcilier ; aucune conclusion de budget complet. |

## Géométrie de référence

Trois STL ont été lus numériquement : Front, Middle, Rear. Leurs étendues brutes sont d’environ 172 unités en largeur. **STL ne porte pas d’unité** ; l’interprétation en millimètres est une hypothèse de travail plausible, non une mesure physique. Les trois pièces n’ont pas la même origine Z : leurs hauteurs ne doivent pas être additionnées comme un empilement établi.

Le script `inspect_sources.py` extrait des sections horizontales et conserve le contour extérieur de plus grande aire. La section sélectionnée de Front est à Z=34,239844 unités source ; son profil simplifié comporte 38 points et mesure 166,3584 ×110,647 unités. Le nouveau profil utilise un facteur `160/166,3584`, pour un encombrement plan nominal de **160 ×106,418 mm**. Il s’agit d’une reconstruction dimensionnelle guidée par l’existant, pas d’une appréciation visuelle du rendu.

Les anciens PCB KiCad ont été parsés en texte : 38 et 37 empreintes, avec plusieurs bibliothèques personnalisées et une architecture Pico historique. Ils ne sont pas réutilisés comme routage ou schéma du nouveau design. L’étendue des points de contrôle Edge.Cuts est 93×84 mm ; elle n’est pas une mesure exhaustive des extrema d’arcs.

## Paramètres encore bloquants

La précision utilisateur ultérieure remplace la disposition initiale : quatre boutons à gauche et quatre à droite, gâchettes de style PS4. [D0.1](disposition-commandes.md) décrit la nouvelle géométrie effective et distingue les propositions de l’agent (sticks plus bas, cotes exactes) de la demande. Deux boutons centraux sont conservés ; L1/R1 exigent deux commandes supplémentaires au BOM. Le budget d’entrées dépend encore du type de capteur L2/R2.

- Référence/révision physique PiSugar 3 Plus, cellule, épaisseur totale, alignement pogo et fixations avec le Pi réel.
- Module casque, jack et boîtier exacts ; le PCM5102A seul n’est pas un amplificateur casque.
- Dessins de joystick, capuchons, gâchettes, contreparties et connecteurs ; course et efforts à confirmer.
- Résolution ADC applicable et empreintes définitives U7/U8 ; topologie de rails et passifs complets.
- Circuit USB autoalimenté, gestion VBUS/charge limitée, CDC et procédé de récupération microSD.
- Position Z et fixation des moteurs, retours mécaniques entre moteurs, dégagement des broches THT et du faisceau.

Ces inconnues n’empêchent pas de discuter les fichiers D0. Elles empêchent de transformer les fichiers en commande de PCB ou impression réputée assemblable.
