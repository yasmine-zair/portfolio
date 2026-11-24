# Portfolio — Yasmine ZAIR

Portfolio personnel (Master 1 Automatique & Robotique, EUPI Clermont-Ferrand) au thème **HUD / sci-fi robotique & IA**.

Le site est **statique** (HTML, CSS, JavaScript, sans dépendances ni étape de build) : il se déploie tel quel sur Vercel ou Render.

## Structure

```
index.html                 page unique (accueil, à propos, parcours, projets, compétences, contact)
css/styles.css             styles du thème
js/main.js                 menu mobile, animations, fond « réseau neuronal »
assets/img/                photo, favicon, illustration de fond robotique-ia-bg.svg
design-system/             design system généré avec le skill ui-ux-pro-max (MASTER.md, tokens)
vercel.json                configuration Vercel
render.yaml                configuration Render (site statique)
```

## Voir le site en local

Ouvrir `index.html` dans le navigateur, ou lancer un petit serveur :

```bash
python -m http.server 8000
# puis http://localhost:8000
```

## Déploiement (à faire plus tard)

1. Créer un dépôt GitHub et y pousser ce dossier.
2. **Vercel** : « Add New Project » → importer le dépôt → Framework Preset : *Other* → pas de commande de build, dossier de sortie : racine → Deploy.
3. **Render** : « New » → « Blueprint » → choisir le dépôt (le fichier `render.yaml` est détecté), ou « Static Site » avec Publish directory `.`.
4. **Neon** : pas nécessaire pour l'instant. Une base Postgres Neon ne servirait que si l'on ajoute plus tard un formulaire de contact qui enregistre les messages (via une fonction serverless Vercel).

## Modifier le contenu

Tout le texte est dans `index.html`. Pour changer l'image de fond de l'accueil, remplacer `assets/img/robotique-ia-bg.svg` (ou modifier `.hero-bg` dans `css/styles.css` pour pointer vers une photo).
