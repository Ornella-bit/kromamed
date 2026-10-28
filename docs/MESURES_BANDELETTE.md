# Mesurer votre bandelette (5 minutes, avec une règle en millimètres)

La carte imprimée a une **fente** pour la bandelette. Les dimensions actuelles sont des **estimations** :
pour que le moteur lise au bon endroit, il faut mettre les mesures de VOTRE bandelette.

Posez une bandelette Multistix 10 SG à plat à côté d'une règle. Notez (en mm) :

| # | Mesure | Valeur estimée actuelle | Votre mesure |
|---|---|---|---|
| 1 | Largeur de la bandelette | 5,5 | |
| 2 | Longueur totale | 95 | |
| 3 | Côté d'une plage colorée (carré) | 4,5 | |
| 4 | Écart entre les centres de 2 plages voisines | 7,0 | |
| 5 | Distance de la POINTE au centre de la 1re plage | 8,0 | |

Quelle est la « pointe » ? C'est l'extrémité qui porte la plage **Leucocytes** (celle qui se lit en dernier, à 2 min).
Vérifiez avec l'étiquette du flacon : l'ordre du haut vers le bas doit être
Leucocytes, Nitrites, Urobilinogène, Protéines, pH, Sang, Densité, Cétones, Bilirubine, Glucose.

Ensuite : ouvrez `kromamed/config.py`, section « Bandelette Multistix 10 SG », et remplacez
`STRIP_W_MM`, `STRIP_LEN_MM`, `PAD_SIZE_MM`, `PAD_PITCH_MM`, `FIRST_PAD_MM` par vos valeurs. Puis :

```
python scripts/make_card.py     # nouvelle carte à imprimer
pytest -q                       # doit afficher 38 passed
```
