# Incident KiCad 8 — reprise native bornée après autorisation

**Mise à jour :** Arthur a autorisé les contrôles/rendus locaux KiCad et FreeCAD portable. La reprise utilise `run_native_check.py`, une opération par sous-processus identifié, limite 20 secondes, arrêt du seul processus créé si délai dépassé. Les assertions ne sont pas désactivées. L’ancien validateur de masse reste gardé.

Sur la carte commandes D0.1 corrigée, `LoadBoard` a terminé en 0,42 seconde, puis un DRC isolé en 0,60 seconde : **0 violation géométrique et 5 connexions manquantes**, attendues sur le connecteur d’une carte non routée. Aucun overflow n’a été observé dans ces essais. Cela ne démontre pas la cause de l’alerte historique. Les résultats sont dans `validation/native-load-controls.json` et `validation/native-current/controls-drc.txt`.

Un incident distinct est survenu lors du premier ERC des nouveaux schémas D1 : sortie Windows `3221225477`, sans rapport. Après ajout des bibliothèques de symboles et tables locales au projet, l’ERC a produit un rapport ; après correction des coordonnées hors grille et déclaration des sources d’alimentation, il a rapporté **0 violation**. L’effet correctif est observé, sans preuve de la cause interne du premier accès mémoire. Les écritures registre tentées par `kicad-cli` ont été refusées ; aucun réglage global n’a été créé par ces essais. Les sections ci-dessous conservent la chronologie de l’incident initial.

Le 22 octobre 2026, Arthur a signalé une fenêtre **wxWidgets Debug Alert** provenant de KiCad 8, avec l’assertion `util.cpp(61) / kimathLogOverflow` et la valeur **3662132882** à convertir en entier. Cette valeur dépasse le maximum signé 32 bits, 2147483647. Le lien temporel avec notre contrôle est fort ; aucune pile d’appel n’a été obtenue pour établir la fonction géométrique exacte.

## Commande et état

La commande suivie était le Python fourni par KiCad 8.0.2 exécutant `tools/validate_design.py`. Elle chargeait nos cartes avec `pcbnew.LoadBoard`, puis appelait `pcbnew.WriteDRCReport`. Aucun lancement de `pcbnew.exe`, visualiseur 3D, navigateur ou rendu n’était demandé. Un appel de bibliothèque natif a néanmoins pu ouvrir cette alerte ; le qualificatif CLI ne garantit donc pas l’absence de fenêtre.

La session d’exécution 67240 a reçu Ctrl+C via le mécanisme du terminal. Elle a retourné **exit 0**, sans session persistante, et deux messages indiquant que les rapports étaient écrits. Cela établit la fin de la commande suivie ; cela ne démontre pas l’absence d’un défaut de calcul. Aucun bouton de la fenêtre n’a été actionné par cet agent et aucun processus tiers n’a été tué.

## Diagnostic textuel et correction conservatrice

Le parsing des fichiers a trouvé des coordonnées finies, de l’ordre de −29,5 à189 mm avant correction, sans valeur géométrique stockée approchant le seuil de conversion. L’erreur n’est donc pas expliquée par une coordonnée directement écrite à plusieurs mètres dans les fichiers.

Treize réservations sur la carte commandes et quatre sur la porteuse étaient représentées par des empreintes sans pads ni formes internes, leurs rectangles étant des dessins de carte. Une bounding box vide est un **candidat explicatif**, pas une cause démontrée. Ces 17 empreintes ont été retirées en texte ; les réservations restent en rectangles et annotations sur les couches de dessin. Le générateur a été corrigé pour ne plus créer de telles empreintes.

Les drivers et leurs condensateurs ont aussi été déplacés en texte pour supprimer les chevauchements simples constatés dans le premier rapport. La vérification textuelle actuelle ne relève plus de chevauchement des boîtes rectangulaires des courtyards avant explicites. Cela ne couvre pas les réservations sans empreinte, les broches sous carte, les câbles ou la mécanique 3D.

## Statut des rapports

Les fichiers `validation/controls-drc.txt`, `base-drc.txt` et `checks.json` décrivent **l’état avant correction textuelle**. Ils indiquaient 21 violations DRC sur commandes, 2 sur porteuse, et 5 connexions manquantes sur chaque carte. Ils sont conservés pour traçabilité, pas comme une approbation des cartes actuelles. Le contrôle natif a terminé, mais sa fiabilité est compromise par l’assertion, et aucun DRC n’a été relancé après correction.

`validation/text-correction-record.json` conserve les hash avant/après. `text-preflight.json` est la vérification textuelle actuelle, indépendante de KiCad et wxWidgets.

## Reprise des contrôles

Les scripts natifs refusent désormais leur lancement normal, avant l’import de `pcbnew`. Le contrôle courant est `preflight_text.py`, qui ne charge aucune bibliothèque graphique. Le drapeau explicite présent dans les scripts natifs n’est **pas une autorisation de reprise** : celle-ci exige d’abord une revue de l’incident et une méthode testée qui remonte les assertions en échec sans dialogue bloquant. Désactiver les assertions pour cacher un dépassement ne constituerait pas une réparation.

Une ouverture manuelle de la copie de consultation reste à l’initiative d’Arthur, qui a demandé à consulter les cartes. L’absence future d’alerte ne peut pas être garantie tant que la cause exacte n’a pas été reproduite et expliquée.
