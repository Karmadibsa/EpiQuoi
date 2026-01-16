# EpiQuoi

EpiQuoi est une application de chat orientée **Epitech** avec :
- un **frontend** React (Vite)
- un **backend** FastAPI qui parle à une IA locale (Ollama)
- un serveur **mcp** (FastAPI) qui expose des “outils” (scraping Epitech)

## Structure du projet

- `Front_End/` : interface (Vite + React)
- `Back_end/` : API IA (FastAPI) + logique d’orchestration
- `mcp/` 

## Démarrage rapide (dev)

### Pré-requis

- Node.js (pour `Front_End/`)
- Python 3.10+ (pour `Back_end/` et `mcp/`)
- Ollama installé + un modèle téléchargé (ex : `ollama pull llama3.2:1b`)

### 1) Lancer le serveur d’outils (`mcp`) — port 8001

```bash
cd mcp
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python server.py
```

Test rapide :
- `http://localhost:8001/healthz`

### 2) Lancer le backend (`Back_end`) — port 8000

Créer `Back_end/.env` (optionnel mais recommandé) :

```env
OLLAMA_MODEL=llama3.1
OLLAMA_URL=http://localhost:11434
```

Puis :

```bash
cd Back_end
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py
```

Endpoints utiles :
- `http://localhost:8000/docs`
- `POST http://localhost:8000/chat`

### 3) Lancer le frontend (`Front_End`) — port 5173

```bash
cd Front_End
npm install
npm run dev
```

Par défaut, le frontend appelle `http://localhost:8000/chat`.
Pour changer l’URL, définir `VITE_API_URL` (voir `Front_End/README.md`).

## Notes

- Si le backend n’est pas joignable, le widget passe en mode “fallback” et demande un **code postal** (côté frontend).
- Le backend appelle `mcp` sur `http://localhost:8001` pour récupérer des infos officielles (campus / formations / pédagogie / valeurs).
