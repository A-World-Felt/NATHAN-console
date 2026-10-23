# NATHAN — revue du port USB-C commun

Codex/OpenAI, agent parent, 22 octobre 2026. Proposition de prototype pour la PR, sans essai matériel ni conformité USB revendiquée.

## Intention et limites

Arthur précise USB-C et confirme l'usage attendu : VBUS vers l'entrée du PiSugar, puis sortie PiSugar vers le Pi ; charge et utilisation simultanées sur secteur. Cela fait évoluer le connecteur micro-B mentionné initialement. Le PiSugar conserve la gestion de batterie. L'interface ajoutée traite la source USB et les données.

PiSugar documente l'utilisation pendant la charge et la charge avec le Pi éteint. La recharge nette dépend de la puissance disponible moins la consommation et les pertes. Le raccordement va à l'entrée 5 V du module, jamais directement à BAT. [Fonctions UPS](https://docs.pisugar.com/docs/product-wiki/battery/ups-intro), [interfaces PiSugar 3](https://docs.pisugar.com/docs/product-wiki/battery/pisugar3/pisugar-3-series).

Le cas batterie vide sur n'importe quel PC standard reste ouvert : Arthur a expliqué son architecture, sans accepter d'exclusion de ce cas. La proposition ne satisfait donc pas encore cette exigence universelle.

## Proposition électrique

`base_usb.py` ajoute 53 composants à la porteuse : USB4105-GF-A, protections de lignes, détection, alimentation des circuits de contrôle, isolation des données et deux chemins d'entrée. Aucun troisième PCB personnalisé.

| Source / état | Comportement prévu |
|---|---|
| USB-C annonçant 3 A | Charge autonome sans Linux, limite nominale 2,381 A. |
| USB-C annonçant 1,5 A | Charge autonome, limite nominale 1,191 A. |
| Chargeur reconnu, courant CC par défaut | Voie conservatrice 377–479 mA calculés ; recharge nette en jouant non garantie. |
| PC standard avant configuration | Charge désactivée ; données si Pi alimenté par batterie. |
| PC standard configuré, budget >=500 mA | Logiciel autorisant la voie 377–479 mA ; courant de contrôle à ajouter. |
| Suspend / déconfiguration | RUN doit être retiré par le logiciel. |
| Débranchement / rebranchement | Autorisation effacée ; un GPIO resté haut ne suffit pas à la restaurer. |
| Batterie vide sur PC sans courant CC accru | Récupération non résolue. |

TUSB320LAI fonctionne en récepteur fixe, mode GPIO, avec Rd internes même sans alimentation. Aucune tension USB-PD supérieure à 5 V n'est demandée. [TI TUSB320LAI](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf).

TPS259470ARPWR gère la voie à courant accru. Deux résistances de 2,80 kΩ ±1 % donnent environ 1,061–1,323 A ou 2,122–2,646 A en combinant ±10 % de limite et ±1 % de résistance, hors consommation de contrôle et transitoires. La voie historique utilise TPS2553 et LM66100 ; elle est désactivée lorsque le courant CC est accru. L'exclusivité est vérifiée en logique stabilisée, pas pendant les délais de commutation. [TI TPS25947](https://www.ti.com/lit/ds/symlink/tps25947.pdf), [TI TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf).

BQ24392 et GOOD_BAT suivent VBUS pour préserver la charge avec Pi éteint. TS3USB30E est alimenté par 3V3_PI pour isoler les données du Pi éteint. Le câble interne exclut le VBUS du Pi. Les deux commutateurs en série et le câble demandent un contrôle d'intégrité USB. [TI BQ24392](https://www.ti.com/lit/ds/slis146d/slis146d.pdf), [TI TS3USB30E](https://www.ti.com/lit/ds/symlink/ts3usb30e.pdf).

La broche ST du LM66100 est physiquement à drain ouvert ; elle est modélisée passive uniquement pour la liaison fixe à GND prescrite lorsqu'elle est inutilisée. Cette exception documentée évite un faux conflit avec le drapeau d'alimentation GND. Aucune erreur ERC n'est exclue globalement. [TI LM66100, broches](https://www.ti.com/lit/ds/symlink/lm66100.pdf).

## Contrat logiciel et preuves

Broches physiques 29/GPIO5 et 31/GPIO6 : `USB_CHARGE_RUN` et `USB_CHARGE_CLOCK`, basses au démarrage. Après configuration USB autorisant le budget, RUN monte puis CLOCK reçoit un front montant. Suspend et déconfiguration remettent RUN à zéro. Ce logiciel reste à implémenter et vérifier sur Pi 3 A+.

Contrôles parent : 128 états de logique stabilisée ; séquence configuration/autorisation/débranchement/rebranchement/suspend ; 53 empreintes chargées par `pcbnew` avec tous les numéros de pastille concordants ; schéma complet de revue à 88 composants physiques, ERC natif KiCad 8.0.2 à zéro erreur et zéro avertissement. Dessin TI RPW0010A consulté visuellement pour l'empreinte locale. Ces contrôles ne prouvent pas l'aptitude à fabriquer.

## Qualification restante

Mesurer courant, température, transitoires inverses, appels de courant et chute de tension avec le PiSugar exact ; vérifier sa stabilité sous limitation d'entrée. L'OVLO nominal de 5,376 V proposé ne prouve pas la protection de la limite de 5,2 V indiquée par PiSugar : tolérances et protection restent à résoudre. Qualifier les transitions entre voies, les changements CC, l'ESD, les courts-circuits CC/VBUS et l'intégrité USB dans les deux orientations. Contrôler pistes, retours, fils et retenue mécanique. Résoudre ou faire accepter explicitement le cas batterie vide sur PC standard.
