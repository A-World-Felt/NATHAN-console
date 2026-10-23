# Reprise Claude — NATHAN en pause

Auteur : Codex/OpenAI, 22 octobre 2026. Arthur demande d’arrêter les nouvelles itérations, de voir l’apparence et de terminer une autre fois. Ne pas reprendre automatiquement le routage.

La PR contient **D1-3 cohérent** : commandes routées, porteuse placée non routée, assemblage synchronisé. Lire le README et `validation/checkpoint-d1-3.json` avant toute commande. Les fichiers historiques D0.1 ne sont pas les cartes courantes.

## Travail local postérieur, non intégré

- `nathan-conception` : commandes nettoyées, SHA `f5e977ddcf64f6acee0a417d151a0f3034b6ba3eedf9c906a29f31fa582e45c6`, 0 erreur/0 liaison ouverte/10 avertissements. Puissance encore à revoir.
- Porteuse expérimentale : SHA `ce6e06de1dc29dd292bcf6dd7d901c55f55d703904ec7bfd86dc7a0405cf3e7e`, 4 erreurs/79 vias pendants/257 liaisons ouvertes. Corriger les échappements avant le routage. `PAD.GetLayer()` s’est révélé inadapté aux pads B.Cu : utiliser leur masque `IsOnLayer`.
- `nathan-integration/power-fix` : essai parent incomplet. Tronc élargi et déplacements locaux partiels, retour GND et cinq nets voisins encore non restaurés. **Ne pas remplacer la carte propre par ce candidat.** Le fichier `controls-before-power.kicad_pcb` conserve l’entrée intacte. Les scripts et logs permettent d’étudier l’essai.
- Les modifications locales de coque/USB et le déplacement C204 n’ont pas été reconstruits dans le STEP/FCStd. Le snapshot3 affichable reste inchangé ; jonction de coques de 3,712 mm³ à corriger.

Les sources locales restent dans `C:/Projects/_codex/vocaux-22`, avec `nathan-conception/REPRISE-NATHAN.md` et `validation/pause-state.json`. Aucun de ces essais ultérieurs n’est présenté comme validé dans la PR. Tous les processus de conception ont été arrêtés ou sont terminés.

## Ordre de reprise conseillé

1. Réviser d’abord la complexité USB-C et le bilan de puissance avec un électronicien ; conserver la distinction entrée charge PiSugar / sortie Pi.
2. Corriger les boucles du convertisseur commandes puis DRC, ERC, correspondance de nets ; terminer le routage porteuse, dont les paires USB et leur retour GND.
3. Exporter les deux STEP à partir des PCB retenus, reconstruire FreeCAD, corriger coque et ouvertures, refaire les contrôles ciblés.
4. Qualifier sur les pièces réelles : dimensions, USB, courant, température, charge, autonomie, audio, haptique et ergonomie. Les résultats logiciels ne remplacent pas ces essais.

Le PiSugar est un module acheté en plus des **deux PCB personnalisés**. Le boîtier de 72 mm est une proposition d’empilement, pas une ergonomie PS4 démontrée. Les composants/réserves incomplets sont identifiés dans la CAO. Aucun jalon n’est déclaré terminé.
