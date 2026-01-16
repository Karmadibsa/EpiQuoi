# EpiQuoi Backend

Backend API pour le chatbot EpiQuoi utilisant FastAPI et Ollama.

## Architecture

Le projet suit une architecture modulaire avec séparation des responsabilités :

```
Back_end/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py             # Configuration et variables d'environnement
│   ├── exceptions.py         # Exceptions personnalisées
│   ├── models/               # Modèles Pydantic
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── routes/               # Routes API
│   │   ├── __init__.py
│   │   └── chat.py
│   ├── services/             # Logique métier
│   │   ├── __init__.py
│   │   ├── chat_service.py           # Orchestration + guardrails + prompt
│   │   ├── campus_service.py         # Client HTTP -> serveur mcp
│   │   ├── degrees_service.py        # Client HTTP -> serveur mcp
│   │   ├── pedagogy_service.py       # Client HTTP -> serveur mcp
│   │   ├── values_service.py         # Client HTTP -> serveur mcp
│   │   ├── geocoding_service.py      # Géocodage / campus le + proche
│   │   └── news_service.py           # Scrapy (nécessite un scraper externe)
│   └── utils/                # Utilitaires
│       ├── __init__.py
│       ├── campus_data.py            # Données + helpers campus (sans coordonnées injectées)
│       ├── epitech_faq.py            # Réponses “FAQ” (ex: méthodologie)
│       ├── geo_utils.py              # Haversine, etc.
│       ├── language_detection.py
│       └── tool_router.py            # Routage d’intentions vers les tools mcp
├── main.py                   # Point d'entrée pour lancer l'application
├── requirements.txt
└── README.md
```

## Installation

1. Installer les dépendances :
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

2. Créer un fichier `.env` à la racine du dossier `Back_end` :
```env
OLLAMA_MODEL=llama3.2:1b
OLLAMA_URL=http://localhost:11434
```

## Utilisation

### Lancer le serveur

```bash
./venv/bin/python main.py
```

Ou avec uvicorn directement :
```bash
./venv/bin/uvicorn app.main:app --reload
```

Le serveur sera accessible sur `http://localhost:8000`

### Documentation API

Une fois le serveur lancé, la documentation interactive est disponible sur :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

### Dépendance: serveur `mcp` (tools)

Le backend appelle le serveur `mcp` sur `http://localhost:8001` pour :
- campus (`POST /scrape/campus`)
- formations/diplômes (`POST /scrape/degrees`)
- pédagogie (`POST /scrape/pedagogy`)
- valeurs (`POST /scrape/values`)

Assure-toi que `mcp/server.py` tourne avant de tester ces fonctionnalités.

## Structure des modules

### `app/config.py`
Gestion centralisée de la configuration avec validation via Pydantic Settings.
Toutes les variables d'environnement sont typées et validées.

### `app/models/schemas.py`
Modèles Pydantic pour la validation des requêtes et réponses API.

### `app/routes/`
Routes FastAPI organisées par domaine fonctionnel.

### `app/services/`
Logique métier isolée dans des services :
- **ChatService** : Orchestration (LLM + tools), gestion d’historique, guardrails anti-hallucination
- **Campus/Degrees/Pedagogy/ValuesService** : Clients HTTP vers `mcp`

### `app/utils/`
Utilitaires réutilisables :
- **campus_data.py** : Données des campus Epitech
- **geo_utils.py** : Fonctions de calcul géographique (distance haversine)
- **language_detection.py** : Détection automatique de la langue
- **tool_router.py** : Routage d’intentions (quand appeler un tool)
- **epitech_faq.py** : Réponses rapides “FAQ”

### `app/exceptions.py`
Exceptions personnalisées pour une meilleure gestion d'erreurs.

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OLLAMA_MODEL` | Modèle Ollama à utiliser | `llama3.1` |
| `OLLAMA_TEMPERATURE` | Température pour la génération | `0.3` |
| `OLLAMA_URL` | URL du serveur Ollama | `http://localhost:11434` |
| `CORS_ORIGINS` | Origines CORS autorisées (séparées par virgule) | `http://localhost:5173,http://127.0.0.1:5173,...` |

## Best Practices implémentées

1. **Séparation des responsabilités** : Chaque module a une responsabilité claire
2. **Configuration centralisée** : Toutes les configs dans `config.py` avec validation
3. **Gestion d'erreurs** : Exceptions personnalisées avec codes HTTP appropriés
4. **Logging structuré** : Utilisation du module `logging` standard

## Tests

Pour ajouter des tests (recommandé) :
```bash
pip install pytest pytest-asyncio httpx
```

## Développement

Le code suit les conventions PEP 8 et utilise :
- FastAPI pour l'API
- Pydantic pour la validation
- Type hints pour la sécurité de type
- Logging pour le débogage
