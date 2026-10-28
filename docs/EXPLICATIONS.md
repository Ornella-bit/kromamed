# Comprendre le code, fichier par fichier

## L'idée en une phrase
Une photo de bandelette change d'aspect selon la lumière. On pose donc la bandelette sur une **carte
imprimée dont on connaît les vraies couleurs** : en voyant comment la photo déforme ces couleurs connues,
on corrige les couleurs de la bandelette, puis on les compare à une table de référence.

## Le trajet d'une photo (`kromamed/pipeline.py`, fonction `analyze`)
1. **Trouver la carte** : 4 repères noir et blanc (ArUco) aux coins.
2. **Redresser** : on remet la carte « bien droite » même si la photo est de travers (homographie).
3. **Corriger la lumière** : le papier doit être blanc partout ; s'il est plus sombre d'un côté, on rattrape.
4. **Contrôler la lumière** : contraste noir/blanc, dominante de couleur, ordre des gris. Le papier blanc est la référence (les couleurs imprimées varient trop d'une imprimante à l'autre).
5. **Contrôler la qualité** : flou, éclairage, repères visibles, bandelette présente… Sous 85 %, **on refuse** et on explique pourquoi.
6. **Lire chaque plage** : couleur médiane de la plage, puis comparaison avec la table de référence.
7. **Rendre le résultat** : niveau (négatif, +, ++…), confiance, ou « indéterminé » si on hésite.

## Les fichiers (`kromamed/`)
| Fichier | Rôle | Quand le modifier |
|---|---|---|
| `config.py` | Tout ce qui se règle : taille de la carte, positions, couleurs de référence, seuils | Changer de bandelette ou de carte |
| `card.py` | Dessine la carte ; détecte les repères ; redresse la photo | Changer la disposition de la carte |
| `illumination.py` | Estime la lumière (surface lisse) et la retire | Rarement |
| `calibration.py` | Contrôles de lumière et de contraste ; détection de la bandelette | Pour régler les seuils |
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

## Livraison 2 : l'API et la page web
- `api/main.py` : un serveur (FastAPI) qui enveloppe le moteur. Il reçoit une photo, appelle `analyze()`,
  et renvoie le résultat en JSON avec les images annotées. Il ne contient AUCUN calcul de vision : tout
  reste dans `kromamed/`. C'est ce qui permettra à une app mobile d'utiliser le même moteur.
- `web/index.html` : la page de démo (HTML + JavaScript, sans framework). Elle appelle l'API avec `fetch`
  et dessine le résultat. Boutons de démonstration = photos simulées par `kromamed/simulate.py`.
- `Dockerfile` : la « recette » pour fabriquer une boîte qui contient le moteur et le serveur ; Render
  la lit pour mettre le site en ligne. `render.yaml` : les réglages de cette mise en ligne.
- `requirements-deploy.txt` : les bibliothèques côté serveur (OpenCV « headless », sans fenêtre).
- `tests/test_api.py` : 11 tests de l'API.

## Livraison 3 : 10 paramètres, rapport, historique
- `kromamed/config.py` décrit maintenant la bandelette **en millimètres** (4 pixels = 1 mm) : largeur, taille et écart
  des plages. Changer de bandelette = changer ces chiffres, puis réimprimer la carte (`scripts/make_card.py`).
- `api/report.py` fabrique le rapport PDF ; `api/exports.py` fabrique l'Excel. Les deux travaillent en mémoire.
- L'historique est gardé dans le navigateur (`localStorage`) : le serveur ne conserve aucune donnée de santé.
- Le minuteur est dans `web/index.html` (JavaScript) : il compte jusqu'à 2 min et sonne à 60 s et 120 s.

## Livraison 4 : l'application mobile (dossier `web/`)
- `index.html` : la structure. Un « écran » par fonction (`s-home`, `s-test`, `s-camera`, `s-result`, `s-history`,
  `s-guide`, `s-profile`) et la barre du bas. Un seul est visible à la fois.
- `static/app.css` : tout le design. Les couleurs sont en haut du fichier (`:root`) : jaune, vert, crème.
- `static/app.js` : le comportement, en 9 parties numérotées (outils, icônes, mémoire du téléphone, messages,
  appels au serveur, navigation, écrans, caméra + minuteur, boutons). Chaque bouton porte `data-act="nom"`
  et la fonction du même nom se trouve dans l'objet `ACT`.
- `sw.js` + `manifest.webmanifest` : permettent d'installer le site comme une application. Le service worker ne met
  JAMAIS l'API en cache.
- `static/icons/`, `static/fonts/` : icônes de l'application et police (hébergée avec le site, licence OFL).
- Le **Profil** (nom, historique, sauvegarde) vit dans `localStorage`, la mémoire du navigateur de votre téléphone.
- **Photo de test (réglage)** : ouvre la caméra sans minuteur et affiche tous les contrôles qualité. C'est l'outil pour
  régler les seuils avec de vraies photos (voir `docs/TESTER_SUR_TELEPHONE.md`).

## Les scripts (`scripts/`)
- `run.py` : analyse une photo, écrit `out/resultat.json` + images (carte redressée, carte corrigée, résultat annoté).
- `benchmark.py` : 100 photos simulées → taux de bonnes lectures + cas qui doivent être refusés.
- `make_card.py` : fabrique l'image de la carte à imprimer.
- `make_demo.py` : crée une photo de démonstration.

## Les tests (`tests/test_pipeline.py`)
22 vérifications automatiques du moteur (+ 16 pour l'API et l'application) : repères trouvés, niveaux retrouvés sous différentes lumières, refus du flou,
refus si un repère est caché, refus d'une ombre forte, refus d'une photo sans carte, couleurs inconnues
déclarées « indéterminées », niveaux de la table assez distincts. `pytest -q` doit afficher `17 passed`.

## Réponses aux questions probables
- **« Pourquoi refuser plutôt que deviner ? »** En santé, un faux résultat est pire qu'une photo à refaire.
- **« Est-ce validé médicalement ? »** Non : c'est une preuve de concept validée sur simulation. La validation
  clinique est la Phase 4 de la feuille de route.
- **« Où est l'IA ? »** Ici : correction colorimétrique + KNN. Le CNN (TFLite) vient en Phase 3, avec des
  vraies photos annotées ; le code actuel est prêt à recevoir ces échantillons (`add_sample`).
