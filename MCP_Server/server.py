import uvicorn

from app.main import create_app
from app.core.settings import get_settings

app = create_app()


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
        stdout_str = stdout.decode()
        try:
            # Essayer de parser directement le JSON
            parsed = json.loads(stdout_str)
            # Si c'est une liste, la retourner directement
            if isinstance(parsed, list):
                return parsed
            # Sinon retourner tel quel
            return parsed
        except json.JSONDecodeError:
            # Si le JSON brut contient des lignes JSON (format Scrapy -O -:json)
            # Essayer de parser ligne par ligne
            lines = stdout_str.strip().split('\n')
            results = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed_line = json.loads(line)
                    if isinstance(parsed_line, dict):
                        results.append(parsed_line)
                except json.JSONDecodeError:
                    continue
            
            if results:
                return results
            else:
                return {"error": "Scrapy n'a pas renvoyé de JSON valide", "raw": stdout_str}
            
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
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())