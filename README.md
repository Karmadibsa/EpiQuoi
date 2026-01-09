# EpiQuoi

EpiQuoi est une application de chat conçue pour les étudiants d'Epitech, dotée d'une interface moderne ressemblant et intégrant une intelligence artificielle locale (Ollama).

## Structure du Projet

Le projet est organisé en trois modules principaux :

- **Front_End/** : L'application React (Vite) pour l'interface utilisateur.
- **Back_end/** : Le serveur Python (FastAPI) qui gère la logique et la communication avec l'IA.
- **MCP_Server/** : Le serveur MCP (Model Context Protocol) pour donner des outils à l'IA (Scraping, etc.) - *En cours de développement*.

## Guide de Démarrage

### Pré-requis

1.  Avoir **Node.js** installé (pour le frontend).
2.  Avoir **Python 3.10+** associé (pour le backend).
3.  Avoir **Ollama** installé et le modèle Mistral téléchargé (`ollama pull mistral`).

### 1. Lancer le Front-End (Interface)

Dans un premier terminal :

```bash
cd Front_End
npm install
npm run dev
```

L'application sera accessible sur `http://localhost:5173`.

### 2. Lancer le Back-End (Serveur IA)

Dans un second terminal :

```bash
cd Back_end
pip install -r requirements.txt
python main.py
```

Le serveur tournera sur `http://localhost:8000`.

### Configuration

Le backend utilise un fichier `.env`. Assurez-vous d'avoir créé ce fichier dans le dossier `Back_end/` avec le contenu suivant :

```env
OLLAMA_MODEL=mistral
OLLAMA_URL=http://localhost:11434
```

## Fonctionnalités Actuelles

*   Chat en temps réel avec une IA locale (Mistral).
*   Interface visuelle "Epitech Blue".
*   Architecture prête pour le Scraping et le MCP.
