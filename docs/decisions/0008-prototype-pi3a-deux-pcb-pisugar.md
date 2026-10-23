# ADR-0008 — Prototype Pi 3 A+, deux PCB et alimentation PiSugar

- Statut : **Proposé**.
- Date : 2026-10-22.
- Auteur : Codex/OpenAI, agent `nathan_bom`, avec intégration et revue par l’agent parent Codex.
- Décideurs attendus : responsables ELEC / ENG / AUDIO et équipe projet.
- Contexte : étude de la nouvelle manette ; ne vaut pas validation de jalon ni autorisation de fabrication.
- Liens : [R-24, R-27, R-49](../specs/REQUIS.md), [C-11, C-29](../specs/CONTRAINTES.md), [cahier des charges §6.4](../specs/CAHIER-DES-CHARGES.md), [ADR-0003](0003-choix-mcu-benchmark-driven.md), [ADR-0005](0005-micropython-mini-jeux-usb-cdc.md), [étude matérielle](../../hardware/pi3a-prototype/README.md).

## Contexte et problème

La nouvelle demande de conception retient un Raspberry Pi 3 Model A+, deux PCB personnalisés reliés entre eux, cinq moteurs en arc, quatre boutons à gauche et quatre à droite, ainsi que des commandes d’épaule et gâchettes de style PS4. La carte des commandes se place au-dessus et vers l’avant de la carte porteuse. Le boîtier doit être reconstruit à partir de l’apparence historique et contenir l’assemblage des cartes et composants.

La réutilisation d’un module PiSugar est demandée pour la batterie et la charge. Après une mention initiale de micro-USB, Arthur précise USB-C pour le port commun de charge et données. Le prototype suit désormais USB-C, cohérent avec R-24. Le choix du calculateur diffère encore du processus de sélection décrit dans ADR-0003. Ces écarts doivent rester visibles ; les ADR acceptés et les exigences existantes ne sont pas réécrits par cette proposition.

## Options envisagées

1. Conserver la sélection MCU historique après benchmark et redessiner l’alimentation : cohérent avec les documents acceptés, mais ne suit pas la nouvelle orientation Pi 3 A+/PiSugar.
2. Prototyper avec Pi 3 A+ et un module PiSugar : réutilise une gestion de batterie existante ; impose de qualifier l’encombrement réel, les contacts, l’autonomie et le chemin USB.
3. Simplifier vers une seule carte personnalisée : réduit les interconnexions, mais ne répond pas à l’architecture mécanique demandée de deux PCB.

## Proposition de conception

Retenir l’option 2 pour une étude de prototype, avec deux cartes personnalisées. Le PiSugar constitue un module supplémentaire acheté, distinct des deux PCB conçus pour NATHAN. PiSugar 3 Plus est le candidat étudié ; ses limites annoncées ne sont pas assimilées à des performances mesurées dans le boîtier.

La disposition des huit boutons de face est explicite. Les deux commandes centrales sont conservées ; la position basse et symétrique des sticks et les dimensions précises des épaules restent des propositions de mise en œuvre. L1/R1 nécessitent deux commandes supplémentaires au BOM. Une variante à L2/R2 analogiques est étudiée pour rester dans le budget d’entrées.

Conserver le contrat USB CDC de l’IDE (ADR-0005, R-49, C-11). Une interface réseau/SSH éventuelle ne remplace pas ce contrat. Séparer le chemin de charge VBUS du chemin de données et de l’alimentation régulée du Pi ; ne pas supposer qu’un port USB de PC permet charge et fonctionnement à pleine puissance simultanément.

La porteuse doit supporter mécaniquement l’ensemble Pi/PiSugar avec une connexion GPIO démontable adaptée à leur empilement. Un connecteur dessiné sous le Pi ne démontre pas, à lui seul, un accouplement possible avec le GPIO supérieur et les contacts PiSugar inférieurs.

L’étude ADC doit satisfaire les 12 bits indiqués au cahier des charges ou soumettre un changement explicite d’exigence ; le MCP3008 à 10 bits du BOM initial ne constitue pas une équivalence.

## Conséquences et limites

- Conserver une largeur nominale maximale de 160 mm ; vérifier ensuite jeux, débattements, fixations, accessibilité tactile et confort sur prototype.
- Produire schémas, connectivité, routage et assemblage CAO éditables, avec statut réel des validations et références de composants documentées.
- Les résultats ERC/DRC portent sur leur révision et leur périmètre exacts. Ils ne démontrent ni l’autonomie de quatre heures, ni les performances audio/haptiques, ni la sécurité de charge du montage réel.
- Les hypothèses dimensionnelles et les composants encore candidats restent identifiés ; une réserve CAO ne vaut pas modèle fabricant qualifié.
- Les exports de consultation ne doivent pas être confondus avec une libération de fabrication.

## Suivi et revue

Revoir les références des sticks/gâchettes, du module audio, de la batterie et du kit PiSugar ; confirmer les courants et le chemin USB ; vérifier l’assemblage, puis les deux cartes sur matériel. Rapprocher le choix Pi 3 A+ du benchmark attendu par ADR-0003 avant d’accepter cette décision.

Le journal existant cite S7-T06 et S7-T07. Le fichier `docs/planning/TACHES.md` n’est pas présent sur la base publique utilisée pour cette PR ; aucun état de tâche ni jalon n’est déclaré terminé ici. Les changements restent attribués à Codex et soumis à la revue de l’équipe, sans modification des décisions acceptées.
