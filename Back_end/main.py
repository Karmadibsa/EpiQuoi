from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(title="EpiChat Backend", version="1.0.0")

# Configuration CORS pour autoriser le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Autoriser le frontend Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de données pour la requête du frontend
class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.get("/")
def read_root():
    return {"status": "online", "message": "EpiChat Backend is running (Local Ollama)"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    
    try:
        # Construction des messages pour Ollama
        messages = [
            {
                'role': 'system',
                'content': "Tu es Hephaestus, un assistant intelligent pour les étudiants d'Epitech. Tu es utile, précis et bienveillant. Tu aides les étudiants à s'orienter et à trouver des informations sur l'école."
            }
        ]
        
        # Ajout de l'historique (si présent)
        # Note: Il faudrait adapter le format de l'historique envoyé par le front
        # pour correspondre exactement à ce qu'attend Ollama (role: user/assistant)
        if request.history:
             messages.extend(request.history)

        # Ajout du message actuel
        messages.append({'role': 'user', 'content': request.message})

        # Appel à Ollama (API locale)
        # Note: Assurez-vous que l'application Ollama tourne sur votre PC
        response = ollama.chat(model=model_name, messages=messages)

        return {
            "response": response['message']['content'],
            "backend_source": f"Ollama Local ({model_name})"
        }

    except Exception as e:
        # Erreur typique : Ollama n'est pas lancé
        print(f"Erreur Ollama: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur de connexion à Ollama. Assurez-vous que l'application Ollama est lancée sur votre PC. Erreur: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
