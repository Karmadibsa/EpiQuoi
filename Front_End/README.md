# EpiQuoi Frontend (Vite + React)

Frontend de l’application EpiQuoi.

## Démarrage (dev)

```bash
cd Front_End
npm install
npm run dev
```

Le frontend est accessible sur `http://localhost:5173`.

## Configuration API

Par défaut, le frontend envoie les messages au backend à :
- `http://localhost:8000/chat`

Tu peux override via une variable d’environnement Vite :

```bash
VITE_API_URL="http://localhost:8000/chat" npm run dev
```

Ou via un fichier `.env` dans `Front_End/` :

```env
VITE_API_URL=http://localhost:8000/chat
```

## Fallback (si le backend est indisponible)

Si `POST /chat` échoue, le widget passe temporairement en mode “fallback” et demande un **code postal**.
Ce comportement est implémenté dans `src/hooks/useChat.js`.

## Docs utiles

- `WIDGET_INTEGRATION.md` : intégration du widget dans une page
- `DEPLOY_GUIDE.md` : déploiement (Netlify, etc.)
