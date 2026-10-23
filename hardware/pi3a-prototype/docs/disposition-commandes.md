# D0.1 — disposition des commandes

Arthur demande explicitement **quatre boutons à gauche, quatre à droite et des gâchettes dans le style d’une manette PS4**. Le placement cardinal précis, les sticks symétriques sous les groupes et la superposition des réserves L1/L2 et R1/R2 sont la proposition de mise en œuvre de l’agent. Les cotes ne constituent pas une validation ergonomique par Arthur.

## Modification effective des sources

La grille précédente de dix boutons est remplacée dans `parameters/design.json`, le PCB commandes et les paramètres OpenSCAD. Le repère conserve Y négatif vers l’avant. Les composants électroniques et les fixations sont déplacés pour laisser la place à cette disposition. La carte porteuse est inchangée.

| Fonction | Références / position proposée en mm |
|---|---|
| Quatre boutons directionnels gauches | SW2 haut (−48,−27), SW3 droite (−32,−11), SW4 bas (−48,5), SW5 gauche (−64,−11) |
| Quatre boutons droits en losange | SW6 haut (48,−27), SW7 droite (64,−11), SW8 bas (48,5), SW9 gauche (32,−11) |
| Deux commandes centrales conservées | SW10 (−15,5,−8), SW11 (15,5,−8) ; fonction finale non inventée |
| Sticks, proposition de placement | (−31,29) et (31,29), réserve 28×28×20 ; empreinte et débattement non qualifiés |
| L1/R1, réserves hautes | Centres XY (±57,−44), Z bas 50, volume alloué 22×10×8 |
| L2/R2, réserves basses | Centres XY (±57,−44), Z bas 32, volume alloué 22×12×16 |

Chaque groupe de face possède quatre points cardinaux, rayon proposé 16 mm. Les empreintes candidates des boutons 12 mm présentent un courtyard de 15,5×14,5 mm ; ce choix explique l’espacement et l’agrandissement de la carte commandes à une étendue de **147×90 mm**. La coque garde sa largeur nominale 160 mm. Ces dimensions d’étude ne prouvent pas le jeu aux parois, la résistance mécanique ou l’accès des doigts.

La coque paramétrique contient désormais les deux groupes, les commandes centrales et les réserves superposées des épaules. Les ouvertures restent désactivées : ni pivots, ressorts, capteurs, fixations des gâchettes, course ni volumes balayés ne sont déterminés. Le style demandé ne permet pas d’inférer une technologie électrique ou une reproduction exacte de pièces Sony.

## Incidence sur le BOM et les entrées

Les dix boutons existants sont affectés à **8 boutons de face + 2 centraux**. L1/R1 ajoutent **deux commandes** à équiper et à ajouter au BOM ; aucune empreinte ni aucun pad supplémentaire n’a été inventé. L2/R2 reprennent les deux fonctions de gâchette déjà présentes dans le projet.

- Si L2/R2 sont analogiques : 10 boutons + 2 clics des sticks + 2 épaules = **14 entrées numériques** ; quatre axes de sticks + deux gâchettes = **6 voies ADC**. Cela occupe les quatorze entrées MCP23017 retenues après prise en compte de la restriction GPA7/GPB7 décrite dans l’analyse BOM.
- Si L2/R2 sont numériques : **16 entrées numériques** sont nécessaires. Il faut alors revoir leur affectation ou le circuit d’extension ; la simple présence de seize broches GPA/GPB ne résout pas la restriction.

Ces comptes sont conditionnels aux deux clics des sticks et à la fonction indépendante des deux épaules. Le type de capteur reste ouvert. Aucun surcoût ni consommation de capteur inconnu n’est ajouté arbitrairement au bilan.

Les cinq moteurs gardent leurs coordonnées en arc. Certains se projettent sous les sticks ; la projection XY ne permet de conclure ni collision ni absence de collision. Leur Z, leurs attaches, les broches traversantes et les faisceaux restent à vérifier.

## Vérifications et état de revue

`sync_controls_text.py` modifie uniquement les origines des 31 empreintes existantes et les dessins de la carte commandes, puis produit les paramètres OpenSCAD. Les pads, nets, bibliothèques embarquées et la porteuse sont conservés. `preflight_text.py` vérifie les deux groupes cardinaux, la concordance des positions PCB/JSON, celle des paramètres OpenSCAD, la symétrie proposée des sticks et les niveaux des épaules.

Le contrôle actuel ne trouve ni référence dupliquée, empreinte vide, nombre géométrique non fini, ni chevauchement de boîtes des courtyards avant explicites. Les deux PCB restent **sans piste ni zone**, sans schéma complet et sans validation électrique. Aucun contrôle natif KiCad, rendu, compilation OpenSCAD ou essai mécanique n’a été relancé. L’incident d’overflow demeure de cause non démontrée.
