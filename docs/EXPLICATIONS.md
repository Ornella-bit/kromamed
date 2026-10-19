# Comprendre le code, fichier par fichier

## L'idée en une phrase
Une photo de bandelette change d'aspect selon la lumière. On pose donc la bandelette sur une **carte
imprimée dont on connaît les vraies couleurs** : en voyant comment la photo déforme ces couleurs connues,
on corrige les couleurs de la bandelette, puis on les compare à une table de référence.

## Le trajet d'une photo (`kromamed/pipeline.py`, fonction `analyze`)
1. **Trouver la carte** : 4 repères noir et blanc (ArUco) aux coins.
2. **Redresser** : on remet la carte « bien droite » même si la photo est de travers (homographie).
3. **Corriger la lumière** : le papier doit être blanc partout ; s'il est plus sombre d'un côté, on rattrape.
4. **Corriger les couleurs** : 10 carrés de couleurs connues servent à calculer une matrice de correction.
5. **Contrôler la qualité** : flou, éclairage, repères visibles… Sous 85 %, **on refuse** et on explique pourquoi.
6. **Lire chaque plage** : couleur médiane de la plage, puis comparaison avec la table de référence.
7. **Rendre le résultat** : niveau (négatif, +, ++…), confiance, ou « indéterminé » si on hésite.

## Les fichiers (`kromamed/`)
| Fichier | Rôle | Quand le modifier |
|---|---|---|
| `config.py` | Tout ce qui se règle : taille de la carte, positions, couleurs de référence, seuils | Changer de bandelette ou de carte |
| `card.py` | Dessine la carte ; détecte les repères ; redresse la photo | Changer la disposition de la carte |
| `illumination.py` | Estime la lumière (surface lisse) et la retire | Rarement |
| `calibration.py` | Calcule la matrice 3x3 de correction des couleurs avec les 10 carrés | Rarement |
| `color.py` | Conversions de couleurs (sRGB, linéaire, L*a*b*) et écart ΔE | Jamais, sauf passer à ΔE2000 |
| `quality.py` | Les 5 contrôles qualité et le score global (le pire gagne) | Recaler les seuils sur de vraies photos |
| `interpreter.py` | Classification KNN : couleur → niveau, avec refus si doute | Phase 3 : ajouter des échantillons mesurés |
| `pipeline.py` | Enchaîne tout | Pour ajouter une étape |
| `simulate.py` | Fabrique de fausses photos réalistes pour tester | Pour tester de nouveaux défauts |

## Trois notions à retenir
- **RGB linéaire** : la lumière « vraie ». Les corrections se font dessus ; l'image d'un téléphone est
  « gamma » et fausserait les calculs.
- **L\*a\*b\*** : un espace de couleurs où la distance mathématique ressemble à la différence perçue par l'œil.
  **ΔE** = cette distance. ΔE < 2 : presque indiscernable.
- **KNN (plus proches voisins)** : on cherche, dans la table, la référence la plus proche de la couleur mesurée.

## Les scripts (`scripts/`)
- `run.py` : analyse une photo, écrit `out/resultat.json` + images (carte redressée, carte corrigée, résultat annoté).
- `benchmark.py` : 100 photos simulées → taux de bonnes lectures + cas qui doivent être refusés.
- `make_card.py` : fabrique l'image de la carte à imprimer.
- `make_demo.py` : crée une photo de démonstration.

## Les tests (`tests/test_pipeline.py`)
17 vérifications automatiques : repères trouvés, niveaux retrouvés sous différentes lumières, refus du flou,
refus si un repère est caché, refus d'une ombre forte, refus d'une photo sans carte, couleurs inconnues
déclarées « indéterminées », niveaux de la table assez distincts. `pytest -q` doit afficher `17 passed`.

## Réponses aux questions probables
- **« Pourquoi refuser plutôt que deviner ? »** En santé, un faux résultat est pire qu'une photo à refaire.
- **« Est-ce validé médicalement ? »** Non : c'est une preuve de concept validée sur simulation. La validation
  clinique est la Phase 4 de la feuille de route.
- **« Où est l'IA ? »** Ici : correction colorimétrique + KNN. Le CNN (TFLite) vient en Phase 3, avec des
  vraies photos annotées ; le code actuel est prêt à recevoir ces échantillons (`add_sample`).
