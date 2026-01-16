# mcp (serveur d’outils)

Ce service expose des endpoints “tools” (scraping Epitech) consommés par le backend (`Back_end/`).

## Démarrage (dev)

```bash
cd mcp
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python server.py
```

Par défaut :
- **host**: `0.0.0.0`
- **port**: `8001`

Test rapide :
- `http://localhost:8001/healthz`

## Endpoints

- `GET /healthz`
- `POST /scrape/campus` (alias `GET /scrape/campus`)
- `POST /scrape/degrees` (alias `GET /scrape/degrees`)
- `POST /scrape/pedagogy` (alias `GET /scrape/pedagogy`)
- `POST /scrape/values` (alias `GET /scrape/values`)

## Variables d’environnement (optionnel)

Le service lit des variables préfixées par `MCP_` (voir `app/core/settings.py`) :
- `MCP_HOST`
- `MCP_PORT`
- `MCP_LOG_LEVEL`
- `MCP_SCRAPE_TIMEOUT_SEC`
- `MCP_USER_AGENT`

## Exemples (curl)

```bash
curl -s http://localhost:8001/healthz
curl -s -X POST http://localhost:8001/scrape/campus | python3 -m json.tool
curl -s -X POST http://localhost:8001/scrape/degrees | python3 -m json.tool
```