# Guide d'Intégration Backend (EpiQuoi)

Ce document détaille les pré-requis techniques pour connecter le Frontend React (EpiQuoi) à votre Backend Python (MCP/Mistral).

## 1. Configuration du Serveur

*   **URL de base** : `http://localhost:8000` (par défaut).
*   **CORS** : Le serveur **DOIT** autoriser `http://localhost:5173`.

## 2. API Endpoints

### `POST /chat`

Endpoint principal de discussion.

#### Requête (Payload JSON)
```json
{
  "message": "C'est quoi la méthodologie Epitech ?"
}
```

#### Réponse (JSON)
```json
{
  "response": "La méthodologie Epitech est basée sur..."
}
```

## 3. Gestion des Erreurs

Si le backend est éteint ou retourne une erreur, le Frontend active automatiquement le mode "Code Postal" pour rediriger l'utilisateur vers un campus physique.

## 4. Exemple FastAPI (Python)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    # Logique LLM ici
    return {"response": f"Echo: {req.message}"}
```
