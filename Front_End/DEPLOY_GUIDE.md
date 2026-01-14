# Guide de Déploiement Multi-Site (Vercel)

Vous pouvez déployer deux versions différentes de l'application à partir du **même dépôt** GitHub en utilisant des variables d'environnement.

## Sites & Variables

Voici les variables à configurer dans Vercel pour lier les deux sites entre eux :

### 1. Site Vitrine + Widget (Par défaut)
C'est le site qui s'affichera si `VITE_APP_MODE` n'est pas "chat".

*   **Variables à ajouter (Settings > Environment Variables)** :
    *   `VITE_FULL_CHAT_URL` : L'URL de votre deuxième site (la version chat plein écran).
        *   *Exemple : https://epichat-app-full.vercel.app*
    *   Cela fera apparaître un bouton **"MODE PLEIN ÉCRAN"** dans le header.

### 2. Application Full Chat (Type ChatGPT)
C'est la version "classique" en plein écran.

*   **Variables à ajouter** :
    *   `VITE_APP_MODE` : **`chat`** (OBLIGATOIRE)
    *   `VITE_SHOWCASE_URL` : L'URL de votre premier site (le site vitrine).
        *   *Exemple : https://epichat-showcase.vercel.app*
    *   Cela fera apparaître un lien **"VOIR LE SITE VITRINE"** dans le header.

---
## Résumé du Workflow

1.  Déployez le **Site 1** (Vitrine) normalement. Notez son URL.
2.  Déployez le **Site 2** (Chat) avec `VITE_APP_MODE=chat`. Notez son URL.
3.  Revenez sur le **Site 1**, ajoutez `VITE_FULL_CHAT_URL` = URL du Site 2. Redéployez.
4.  Revenez sur le **Site 2**, ajoutez `VITE_SHOWCASE_URL` = URL du Site 1. Redéployez.

---

## Instructions Netlify

J'ai déjà ajouté un fichier `netlify.toml` à la racine pour faciliter la configuration.

### Site 1 : Vitrine (Showcase)
1.  Connectez votre dépôt GitHub sur Netlify.
2.  Configuration de Build (normalement automatique grâce au fichier toml) :
    *   **Base directory** : `Front_End`
    *   **Build command** : `npm run build`
    *   **Publish directory** : `dist`
3.  Déployez le site.
4.  Une fois l'URL obtenue (ex: `https://epitech-showcase.netlify.app`), allez dans **Site configuration > Environment variables**.
5.  Ajoutez `VITE_FULL_CHAT_URL` avec l'URL de votre futur Site 2.

### Site 2 : Full Chat
1.  Créez un **"New site aliases"** ou un nouveau site pointant sur le **MÊME dépôt GitHub**.
2.  Mêmes paramètres de build.
3.  Allez dans **Site configuration > Environment variables**.
4.  Ajoutez :
    *   `VITE_APP_MODE` = `chat`
    *   `VITE_SHOWCASE_URL` = L'URL de votre Site 1.
5.  Déployez le site.
