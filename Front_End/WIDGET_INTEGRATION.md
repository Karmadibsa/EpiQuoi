# Guide d'Intégration du Widget EpiChat

Ce guide explique comment intégrer le widget de chat **EpiChat** dans une autre application React.

## 1. Fichiers Nécessaires

Pour que le widget fonctionne, vous devez copier les dossiers et fichiers suivants dans votre projet cible (par exemple dans `src/`) :

*   **Composants** (`src/components/`) :
    *   `ChatWidget.jsx` (Le bouton flottant et le conteneur)
    *   `WidgetChat.jsx` (L'interface du chat version widget)
    *   `Message.jsx` (L'affichage des messages)
    *   `DotGrid.jsx` (Optionnel, si utilisé dans le design)
*   **Hooks** (`src/hooks/`) :
    *   `useChat.js` (Toute la logique conversationnelle)
*   **Services** (`src/services/`) :
    *   `api.js` (Communication avec le backend)
    *   `constants.js` (Données statiques comme les campus)

## 2. Dépendances

Assurez-vous que votre projet installe les bibliothèques suivantes (utilisées pour les icônes et les animations) :

```bash
npm install lucide-react framer-motion
```

## 3. Configuration Tailwind CSS

Le design repose sur **Tailwind CSS**. Assurez-vous que votre fichier `tailwind.config.js` inclut les couleurs personnalisées d'Epitech :

```javascript
// tailwind.config.js
export default {
    theme: {
        extend: {
            colors: {
                epitech: {
                    blue: '#013afb',
                    green: '#00ff97',
                    pink: '#ff1ef7',
                    purple: '#ff5f3a',
                    dark: '#141414',
                    gray: '#f3f4f6',
                }
            },
            fontFamily: {
                heading: ['Anton', 'sans-serif'],
                body: ['"IBM Plex Sans"', 'sans-serif'],
            },
        },
    },
    // ...
}
```

*Note : N'oubliez pas d'importer les polices (Google Fonts : Anton & IBM Plex Sans) dans votre CSS global ou votre `index.html`.*

## 4. Utilisation

Il suffit ensuite d'importer et d'ajouter le composant `<ChatWidget />` à la racine de votre application (ou dans un layout global) :

```jsx
import React from 'react';
import ChatWidget from './components/ChatWidget';

function App() {
  return (
    <div className="App">
      {/* Votre contenu existant... */}
      <h1>Mon Site Web</h1>
      
      {/* Le Widget se positionnera tout seul en bas à droite */}
      <ChatWidget />
    </div>
  );
}

export default App;
```

## 5. Backend

Le widget attend que le backend tourne localement sur `http://localhost:8000/chat`. 
Pour modifier cette URL, éditez le fichier `src/services/api.js` ou configurez la variable d'environnement `VITE_API_URL`.
