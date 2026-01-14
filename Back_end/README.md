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
│   │   ├── chat_service.py
│   │   ├── geocoding_service.py
│   │   └── news_service.py
│   └── utils/                # Utilitaires
│       ├── __init__.py
│       ├── campus_data.py
│       ├── geo_utils.py
│       └── language_detection.py
├── main.py                   # Point d'entrée pour lancer l'application
├── requirements.txt
└── README.md
```

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Créer un fichier `.env` à la racine du dossier `Back_end` :
```env
OLLAMA_MODEL=llama3.1
```

## Utilisation

### Lancer le serveur

```bash
python main.py
```

Ou avec uvicorn directement :
```bash
uvicorn app.main:app --reload
```

Le serveur sera accessible sur `http://localhost:8000`

### Documentation API

Une fois le serveur lancé, la documentation interactive est disponible sur :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

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
- **ChatService** : Gestion des interactions avec Ollama, détection d'intentions, construction des prompts
- **GeocodingService** : Recherche du campus le plus proche basée sur la localisation
- **NewsService** : Récupération des actualités Epitech via Scrapy

### `app/utils/`
Utilitaires réutilisables :
- **campus_data.py** : Données des campus Epitech
- **geo_utils.py** : Fonctions de calcul géographique (distance haversine)
- **language_detection.py** : Détection automatique de la langue

### `app/exceptions.py`
Exceptions personnalisées pour une meilleure gestion d'erreurs.

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OLLAMA_MODEL` | Modèle Ollama à utiliser | `llama3.1` |
| `OLLAMA_TEMPERATURE` | Température pour la génération | `0.3` |
| `CORS_ORIGINS` | Origines CORS autorisées (séparées par virgule) | `http://localhost:5173,http://127.0.0.1:5173` |

## Best Practices implémentées

1. **Séparation des responsabilités** : Chaque module a une responsabilité claire
2. **Configuration centralisée** : Toutes les configs dans `config.py` avec validation
3. **Gestion d'erreurs** : Exceptions personnalisées avec codes HTTP appropriés
4. **Logging structuré** : Utilisation du module `logging` standard
5. **Validation des données** : Modèles Pydantic pour toutes les entrées/sorties
6. **Type hints** : Typage complet pour une meilleure maintenabilité
7. **Documentation** : Docstrings sur toutes les fonctions et classes
8. **Modularité** : Code réutilisable et testable

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
