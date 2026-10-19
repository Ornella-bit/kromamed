# Mettre KromaMed en ligne (Render, gratuit)

Résultat : une adresse du type `https://kromamed.onrender.com` à donner au jury, ouverte sur ordinateur
ET sur téléphone (le bouton « Prendre une photo » ouvre l'appareil photo).

## Avant de commencer
- Le projet est sur GitHub (voir README, section 3) et contient `Dockerfile`, `render.yaml`, `requirements-deploy.txt`.
- Les tests passent en local : `pytest -q` → `28 passed`.

## Étapes
1. Allez sur **render.com** → **Get Started** → connectez-vous avec votre compte **GitHub**.
2. **+ New → Web Service** → choisissez votre dépôt `kromamed` (autorisez Render à y accéder si demandé).
3. Vérifiez les champs :
   - **Language / Runtime** : `Docker` (Render détecte le `Dockerfile`)
   - **Instance Type** : `Free`
   - **Branch** : `main`
4. Cliquez **Create Web Service**. La première construction prend quelques minutes (suivez les « logs »).
5. Quand le statut passe à **Live**, cliquez sur l'adresse affichée en haut. Testez :
   - un bouton de démonstration (ex. « Protéinurie »),
   - `…/api/health` (doit afficher `{"status":"ok"...}`),
   - `…/docs` (documentation interactive de l'API, bon point pour le jury).

Alternative : **New → Blueprint** utilise directement `render.yaml`.

## À savoir (important pour le jour J)
- **Mise en veille** : le gratuit s'endort après 15 minutes sans visite ; le réveil prend de quelques secondes
  à environ une minute. **Ouvrez l'adresse 5 minutes avant de présenter.**
- **Puissance limitée** : l'offre gratuite est très petite (512 Mo, 0,1 CPU). L'analyse peut prendre quelques
  secondes au lieu de 0,2 s. C'est normal ; ce n'est pas la performance finale du moteur.
- **Mises à jour** : chaque `git push` sur `main` redéploie automatiquement.
- Si le déploiement échoue : ouvrez l'onglet **Logs** et copiez-moi la dernière erreur.

## Tester Docker en local (facultatif, nécessite Docker Desktop)
```bash
docker build -t kromamed .
docker run -p 8000:7860 kromamed
# ouvrir http://localhost:8000
```

## Autre hébergeur possible : Hugging Face Spaces (type « Docker »)
Même `Dockerfile` (port 7860 par défaut). Il faut ajouter en tête du `README.md` un bloc
`sdk: docker` et `app_port: 7860`. Vérifiez la procédure actuelle sur la documentation de Hugging Face avant.
