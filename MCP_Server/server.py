import os
import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# --- 1. CONFIGURATION DU SERVEUR WEB ---
app = FastAPI()

# Le fameux "Tapis Rouge" pour React (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # On autorise tout le monde pour tester (plus simple)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. LES OUTILS (TOOLS) ---

async def run_scrapy_spider():
    """Lance le scraper et récupère le JSON"""
    project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "epitech_scraper")
    # Commande pour lancer le spider et sortir le résultat en JSON standard
    command = "scrapy crawl campus_spider -O -:json --nolog"
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_path
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {"error": stderr.decode()}
        
        # On essaie de lire le JSON retourné par Scrapy
        try:
            return json.loads(stdout.decode())
        except:
            return {"error": "Scrapy n'a pas renvoyé de JSON valide", "raw": stdout.decode()}
            
    except Exception as e:
        return {"error": str(e)}

# --- 3. LES ROUTES (Ce que React appelle) ---

# Route simple pour vérifier que le serveur est en vie
@app.get("/")
def read_root():
    return {"status": "Online", "message": "Le Cerveau Python est prêt 🧠"}

@app.post("/scrape/campus")
async def scrape_campus_endpoint():
    """Trigger the campus spider and return JSON results."""
    print("🕷️ Triggering Campus Spider via API...")
    data = await run_scrapy_spider()
    print(f"🕷️ [MCP] Scraper Data: {data}")
    return data

# Route CHAT (Celle qui bloquait en rouge sur ton écran)
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("messages", []) # React envoie souvent une liste "messages"
    
    # Récupérer le dernier message de l'utilisateur
    last_msg = ""
    if isinstance(user_message, list) and len(user_message) > 0:
        last_msg = user_message[-1].get("content", "").lower()
    elif isinstance(user_message, str):
        last_msg = user_message.lower()

    # --- LOGIQUE SIMPLE DE TEST ---
    # Si l'utilisateur parle de "campus" ou "école", on lance le scraper
    if "campus" in last_msg or "ecole" in last_msg or "ville" in last_msg:
        print("🤖 Détection mot-clé : Lancement du Scraper...")
        campus_data = await run_scrapy_spider()
        
        # On formate la réponse pour React
        return {
            "role": "assistant",
            "content": f"Voici les données fraîches récupérées sur le site d'Epitech :\n\n{json.dumps(campus_data, indent=2, ensure_ascii=False)}"
        }
    
    # Sinon, réponse par défaut
    return {
        "role": "assistant",
        "content": f"J'ai bien reçu ton message : '{last_msg}'. \n(Pour tester le scraper, demande-moi : 'Quels sont les campus ?')"
    }

# --- 4. LANCEMENT ---
if __name__ == "__main__":
    print("🚀 Serveur lancé sur http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)