# Protocole d'utilisation et temps de lecture

## Les 5 étapes (à afficher dans l'application)
1. **Préparation** : urine fraîche, récipient propre et sec ; carte d'étalonnage imprimée à plat.
2. **Immersion** : toutes les plages dans l'urine pendant 1 seconde maximum, puis démarrer le minuteur.
3. **Séchage** : effleurer le bord de la bandelette sur un papier absorbant (évite que les réactifs ne bavent).
4. **Mise en place** : bandelette dans la fente de la carte, pointe en haut.
5. **Photo** : à 60 s, téléphone à plat, lumière naturelle homogène, sans flash, 4 repères visibles.

La règle millimétrée du protocole initial n'est plus nécessaire : la carte d'étalonnage donne l'échelle et les couleurs.

## Temps de lecture du fabricant (Multistix 10 SG)
| Temps | Plages |
|---|---|
| 30 s | Glucose, bilirubine |
| 40 s | Cétones |
| 45 s | Densité |
| 60 s | Sang, pH, protéines, urobilinogène, nitrites |
| 2 min | Leucocytes |

Une photo unique à 60 s est un **compromis** : les leucocytes peuvent être sous-estimés, le glucose et la
bilirubine sur-estimés. Voie d'amélioration : 2 photos (60 s et 2 min) en ne retenant que les leucocytes de la 2e.

## Ce qui a été repris des documents reçus
- Les 10 paramètres et leur ordre (étiquette Multistix 10 SG), le parcours en 5 étapes, le minuteur de 60 s,
  le modèle de rapport PDF et les colonnes du fichier Excel `base_donnees_tests.xlsx`.

## Ce qui n'a PAS été repris, et pourquoi
- **Le `api.py` des documents renvoie un résultat écrit en dur** (« Leucocytes : Positif (++) ») quelle que soit la photo.
  À ne jamais présenter comme une vraie analyse. Notre API appelle le vrai moteur.
- **Le tri `sorted(NUANCIER.keys())`** classe « 10_Glucose » juste après « 1_Leucocytes » : les plages seraient lues
  dans le mauvais ordre. Notre ordre est explicite (`config.PARAMS`).
- **La détection de la bandelette seule** (contours sur image en gris, sans seuillage) est fragile et ne corrige
  ni la lumière ni les couleurs. La carte d'étalonnage le fait.
- **Écriture des patients dans un Excel sur le serveur** : disque éphémère chez l'hébergeur gratuit, risque de perte,
  et données médicales stockées. À la place : historique dans le navigateur + export Excel à la demande.
- **Le code Flutter** (non intégré à ce stade) contient des erreurs à corriger (import `pdf/Pdf.dart`, paramètre
  `cross:`) et n'a pas de vraie caméra (un texte « Flux Caméra Actif »).
- **Couleurs du nuancier** : ce sont des valeurs de simulation (certaines manquantes dans le PDF). Les nôtres sont
  complètes mais aussi de démonstration : seules des mesures sur de vraies bandelettes feront foi.
