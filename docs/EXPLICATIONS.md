# Comprendre le code, fichier par fichier

## L'idée en une phrase
Une photo de bandelette change d'aspect selon la lumière. On pose donc la bandelette sur une **carte imprimée à papier
blanc** : le papier blanc, visible dans la même photo, sert de référence pour corriger la lumière et sa teinte. On lit
ensuite la couleur de chaque plage et on la compare à une table de référence.

## Le trajet d'une photo (`kromamed/pipeline.py`, fonction `analyze`)
1. **Trouver la carte** : 4 repères noir et blanc (ArUco) aux coins.
2. **Redresser** : on remet la carte « bien droite » même si la photo est de travers (homographie).
3. **Corriger la lumière** : le papier doit être blanc partout ; s'il est plus sombre d'un côté, on rattrape
   (surface lisse estimée sur les pixels de papier, puis division de l'image par cette surface).
4. **Contrôler la lumière** : contraste noir/blanc des repères, dominante de couleur du papier, ordre des 5 gris.
5. **Lire chaque plage** : couleur médiane de la plage, convertie en L*a*b*.
6. **Contrôler la qualité** : 6 critères (repères visibles, netteté, exposition, éclairage uniforme, lumière et
   contraste, bandelette présente). Le pire gagne : sous 85 %, **on refuse** et on explique pourquoi.
7. **Classer et rendre le résultat** : niveau le plus proche (négatif, +, ++…), indice de confiance, ou
   « indéterminé » si deux niveaux sont trop proches.

## Pourquoi le papier blanc et pas les couleurs imprimées ? (l'histoire à raconter)
Une première version forçait les couleurs imprimées de la carte vers leurs valeurs « idéales ». Un test avec une **vraie
carte imprimée** a montré que l'imprimante s'écarte beaucoup de l'idéal (un vert 4 fois plus sombre, des gris teintés) :
l'étalonnage tombait à 0 % et déformait les couleurs. La référence est donc maintenant le **papier blanc** ; les carrés de
gris et de couleur servent seulement de contrôles. Autre conséquence : une carte **vide** (sans bandelette) est refusée
au lieu d'être lue comme un résultat « normal ».

## Les fichiers du moteur (`kromamed/`)
| Fichier | Rôle | Quand le modifier |
|---|---|---|
| `config.py` | Tout ce qui se règle : taille de la carte, positions des plages, couleurs de référence, seuils | Changer de bandelette ou de carte |
| `card.py` | Dessine la carte ; détecte les repères ; redresse la photo | Changer la disposition de la carte |
| `illumination.py` | Estime la lumière (surface lisse) et la retire ; mesure l'écart à cette surface | Rarement |
| `calibration.py` | Contrôles de lumière et de contraste ; détection de la bandelette | Pour régler les seuils |
| `color.py` | Conversions de couleurs (sRGB, linéaire, L*a*b*) et écart ΔE | Jamais, sauf passer à ΔE2000 |
| `quality.py` | Les 6 contrôles qualité et le score global (le pire gagne) | Recaler les seuils sur de vraies photos |
| `interpreter.py` | Classification KNN : couleur → niveau, avec refus si doute | Phase 3 : ajouter des échantillons mesurés |
| `pipeline.py` | Enchaîne tout | Pour ajouter une étape |
| `simulate.py` | Fabrique de fausses photos réalistes pour tester | Pour tester de nouveaux défauts |
| `drawing.py` | Petit outil de dessin compatible OpenCV 4 et 5 | Jamais |

## Le serveur (`api/`) et l'application (`web/`)
- `api/main.py` : serveur FastAPI. Il reçoit la photo, appelle `analyze()` et renvoie le résultat en JSON avec des
  images annotées. Il ne contient **aucun calcul de vision** : tout reste dans `kromamed/`.
- `api/report.py` (rapport PDF) et `api/exports.py` (export Excel) travaillent **en mémoire** : rien n'est conservé.
- `web/index.html` : la structure. Un « écran » par fonction (`s-home`, `s-test`, `s-camera`, `s-result`, `s-history`,
  `s-guide`, `s-profile`) et la barre du bas. Un seul est visible à la fois.
- `web/static/app.css` : tout le design. Les couleurs sont en haut du fichier (`:root`) : jaune, vert, crème.
- `web/static/app.js` : le comportement, en 9 parties numérotées (outils, icônes, mémoire du téléphone, messages,
  appels au serveur, navigation, écrans, caméra + minuteur, boutons). Chaque bouton porte `data-act="nom"` et la
  fonction du même nom se trouve dans l'objet `ACT`. Le bouton « Retour » suit la hiérarchie sous-page → onglet →
  accueil → sortie.
- `web/sw.js` + `web/manifest.webmanifest` : rendent le site installable comme une application. Le service worker ne met
  **jamais** l'API en cache (données de santé).
- Le **Profil** (nom) et l'**historique** vivent dans `localStorage`, la mémoire du navigateur du téléphone.
- **Photo de test (réglage)** : ouvre la caméra sans minuteur, n'exige pas de bandelette, et affiche les 6 contrôles
  qualité en détail (voir `docs/TESTER_SUR_TELEPHONE.md`).
- `Dockerfile` + `render.yaml` : la « recette » pour mettre le site en ligne sur Render à chaque envoi sur GitHub.

## Trois notions à retenir
- **RGB linéaire** : la lumière « vraie ». Les corrections se font dessus ; l'image d'un téléphone est
  « gamma » et fausserait les calculs.
- **L\*a\*b\*** : un espace de couleurs où la distance mathématique ressemble à la différence perçue par l'œil.
  **ΔE** = cette distance. ΔE < 2 : presque indiscernable.
- **KNN (plus proches voisins)** : on cherche, dans la table, la référence la plus proche de la couleur mesurée.

## Les scripts (`scripts/`) et les tests (`tests/`)
- `run.py` : analyse une photo, écrit `out/resultat.json` + images (carte redressée, corrigée, résultat annoté).
- `benchmark.py` : 100 photos simulées → taux de bonnes lectures + cas qui doivent être refusés.
- `make_card.py` : fabrique la carte à imprimer (PDF A4, taille réelle). `make_demo.py` : photo de démonstration.
- 38 tests automatiques (`pytest -q` doit afficher `38 passed`) : 22 pour le moteur et 16 pour l'API et l'application.
  Ils vérifient notamment : repères trouvés, niveaux retrouvés sous différentes lumières, refus du flou, d'un repère
  caché, d'une ombre forte, d'une carte sans bandelette, et le test sur une **vraie photo** de carte imprimée.

## Réponses aux questions probables
- **« Pourquoi refuser plutôt que deviner ? »** En santé, un faux résultat est pire qu'une photo à refaire.
- **« Est-ce validé médicalement ? »** Non : c'est une preuve de concept validée sur simulation et sur une vraie carte
  imprimée. La validation clinique est la Phase 4 de la feuille de route.
- **« Où est l'IA ? »** Vision par ordinateur (trouver, redresser, corriger) + KNN pour classer les couleurs, avec un
  indice de confiance. Le réseau de neurones (TFLite) vient en Phase 3, avec de vraies photos annotées ; le code actuel est prêt à recevoir ces échantillons (`add_sample`).