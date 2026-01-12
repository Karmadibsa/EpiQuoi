from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import os
from dotenv import load_dotenv
import httpx
import math

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

import subprocess
import json

# ... (rest of imports)

# Fonction Tool pour récupérer les news
def get_epitech_news():
    try:
        # Chemin absolu vers le projet scrapy - A adapter selon votre structure précise
        scraper_path = os.path.join(os.path.dirname(__file__), "../MCP_Server/epitech_scraper")
        
        # Lancer le spider et sortir le résultat dans un fichier temporaire (ou stdout)
        # Ici on écrase news.json à chaque fois pour avoir du frais
        subprocess.run(["python", "-m", "scrapy", "crawl", "epitech_news", "-O", "news.json"], 
                       cwd=scraper_path, check=True, capture_output=True)
        
        # Lire le fichier json
        with open(os.path.join(scraper_path, "news.json"), "r", encoding="utf-8") as f:
            news_data = json.load(f)
            
        # Formater pour l'IA
        formatted_news = "Voici les dernières actualités Epitech récupérées en direct :\n"
        for item in news_data[:3]: # Top 3
            title = item['title'].strip() if item['title'] else "Sans titre"
            summary = item['summary'].strip() if item['summary'] else ""
            link = item['link']
            formatted_news += f"- {title}: {summary} (Source: {link})\n"
            
        return formatted_news

    except Exception as e:
        return f"Erreur lors de la récupération des news : {str(e)}"

# ... (existing imports)

# Données des campus Epitech avec coordonnées APPROXIMATIVES (Lat, Lon)
CAMPUSES = {
    "Paris": {"zip": "94270", "addr": "24 rue Pasteur, 94270 Le Kremlin-Bicêtre", "coords": (48.8156, 2.3631), "email": "paris@epitech.eu", "phone": "01 44 08 00 60"},
    "Bordeaux": {"zip": "33000", "addr": "81-89 Rue du Jardin public, 33000 Bordeaux", "coords": (44.8432, -0.5756), "email": "bordeaux@epitech.eu", "phone": "05 64 13 05 84"},
    "Lille": {"zip": "59000", "addr": "5-9 Rue du Palais Rihour, 59000 Lille", "coords": (50.6359, 3.0617), "email": "lille@epitech.eu", "phone": "03 74 09 16 24"},
    "Lyon": {"zip": "69000", "addr": "86 Boulevard Marius Vivier Merle, 69003 Lyon", "coords": (45.7597, 4.8584), "email": "lyon@epitech.eu", "phone": "04 28 29 33 25"},
    "Marseille": {"zip": "13000", "addr": "21 Rue Marc Donadille, 13013 Marseille", "coords": (43.3444, 5.4243), "email": "marseille@epitech.eu", "phone": "04 84 89 13 54"},
    "Montpellier": {"zip": "34000", "addr": "16 Boulevard des Arceaux, 34000 Montpellier", "coords": (43.6095, 3.8687), "email": "montpellier@epitech.eu", "phone": "04 11 93 17 52"},
    "Nantes": {"zip": "44000", "addr": "18 Rue Flandres-Dunkerque, 44000 Nantes", "coords": (47.2156, -1.5552), "email": "nantes@epitech.eu", "phone": "02 85 52 28 71"},
    "Nancy": {"zip": "54000", "addr": "80 Rue Saint-Georges, 54000 Nancy", "coords": (48.6923, 6.1848), "email": "nancy@epitech.eu", "phone": "03 72 47 11 50"},
    "Nice": {"zip": "06000", "addr": "13 Rue Saint-François de Paule, 06300 Nice", "coords": (43.6961, 7.2718), "email": "nice@epitech.eu", "phone": "04 22 13 32 66"},
    "Rennes": {"zip": "35000", "addr": "19 Rue Jean-Marie Huchet, 35000 Rennes", "coords": (48.1130, -1.6738), "email": "rennes@epitech.eu", "phone": "02 57 22 08 54"},
    "Strasbourg": {"zip": "67000", "addr": "4 Rue du Dôme, 67000 Strasbourg", "coords": (48.5831, 7.7479), "email": "strasbourg@epitech.eu", "phone": "03 67 10 28 83"},
    "Toulouse": {"zip": "31000", "addr": "40 Boulevard de la Marquette, 31000 Toulouse", "coords": (43.6125, 1.4287), "email": "toulouse@epitech.eu", "phone": "05 82 95 79 93"},
}

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon de la Terre en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_nearest_campus(user_zip):
    try:
        # 1. Obtenir les coordonnées GPS du code postal via API Gouv
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api-adresse.data.gouv.fr/search/?q={user_zip}&limit=1")
            data = resp.json()
            
        if not data.get('features'):
            return None
            
        user_coords = data['features'][0]['geometry']['coordinates'] # [lon, lat]
        user_lon, user_lat = user_coords[0], user_coords[1]
        
        # 2. Trouver le campus le plus proche (Distance Haversine)
        min_dist = float('inf')
        nearest = None
        
        for city, info in CAMPUSES.items():
            camp_lat, camp_lon = info['coords']
            dist = haversine_distance(user_lat, user_lon, camp_lat, camp_lon)
            if dist < min_dist:
                min_dist = dist
                nearest = (city, info)
                
        # On injecte la distance dans info pour l'utiliser plus tard
        if nearest:
            nearest[1]['dist'] = int(min_dist)

        return nearest # (City, Data)
    except Exception as e:
        print(f"Erreur Geo: {e}")
        return None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    model_name = os.getenv("OLLAMA_MODEL", "llama3.1")
    
    # SYSTEME DE TOOLING BASIQUE (MCP-like)
    # Détection d'intention simplifiée
    keywords_news = ["news", "actualité", "actu", "nouveauté", "événement"]
    context_extra = ""
    backend_source = f"Ollama Local ({model_name})"
    
    msg_lower = request.message.lower()

    # Tool 1: News Scraper
    if any(k in msg_lower for k in keywords_news) and "epitech" in msg_lower:
        print("🔍 Tool Activation: Scraper Epitech News")
        news_info = get_epitech_news()
        context_extra += f"\n\n[SYSTÈME: DONNÉES LIVE INJECTÉES]\n{news_info}\nUtilise ces informations pour répondre."
        backend_source += " + Scraper"

    # Tool 2: Campus Finder (Détection de Code Postal)
    import re
    location_query = None
    
    # 1. Regex Code Postal (5 chiffres)
    zip_match = re.search(r'\b\d{5}\b', request.message)
    if zip_match:
        location_query = zip_match.group(0)
    else:
        # 2. Regex Ville (ex: "habite à Metz", "suis de Lyon")
        city_match = re.search(r'(?i)(?:habite|vivre|suis|campus|ville|vers)\s+(?:à|a|de|sur)\s+([a-zA-Z\u00C0-\u00FF\s\-]+)', request.message)
        if city_match:
            # On prend le premier mot ou groupe de mots significatif
            captured = city_match.group(1).strip()
            # Nettoyage brutal: si on a "Metz j", on garde "Metz"
            # On split sur l'espace et on garde les morceaux qui sont plus longs que 1 char (sauf "Le" etc)
            parts = captured.split()
            cleaned_parts = []
            for p in parts:
                if len(p) > 2 or p.lower() in ["le", "la", "les", "san", "los", "new"]:
                    cleaned_parts.append(p)
                else:
                    break # Dès qu'on tombe sur un mot bizarre ("j", "et"), on arrête
            
            if cleaned_parts:
                location_query = " ".join(cleaned_parts)
            else:
                 location_query = parts[0] if parts else None

    if location_query:

        print(f"🔍 Tool Activation: Campus Finder (Query: {location_query})")
        near_campus = await get_nearest_campus(location_query)
        if near_campus:
            city, data = near_campus
            dist_km = int(data.get('dist', 0)) if 'dist' in data else 0 # You might need to add distance to return of get_nearest_campus if not there, otherwise assume it is handled or calculate it.
            # Actually get_nearest_campus returns (city, info). let's add distance to return or just handle logic here.
            # wait, get_nearest_campus returns (city, info). info has 'coords'.
            # Let's just trust variable names.
            
            is_same_city = location_query.lower() in city.lower() or city.lower() in location_query.lower()

            context_extra += (
                f"\n\n[SYSTÈME: LOCALISATION DÉTECTÉE]\n"
                f"L'utilisateur est localisé à : {location_query.upper()}.\n"
                f"Le campus Epitech LE PLUS PROCHE est à : {city.upper()} (Distance: {dist_km} km).\n"
                f"Coordonnées de {city}: {data['addr']}.\n"
                f"Contact {city}: {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}\n"
            )
            
            if not is_same_city and dist_km > 5: # Si > 5km de différence
                 context_extra += (
                    f"\n/!\\ ALERTE HALLUCINATION /!\\\n"
                    f"IL N'Y A PAS DE CAMPUS EPITECH À {location_query.upper()} ! NE L'INVENTE PAS.\n"
                    f"TU DOIS DIRE : 'Même si tu es à {location_query}, le campus le plus proche est celui de {city}.'\n"
                    f"INTERDICTION DE DONNER UNE ADRESSE OU UN TÉLÉPHONE À {location_query}.\n"
                    f"DONNE UNIQUEMENT LES INFOS DE {city}.\n"
                 )
            
            context_extra += f"Si l'utilisateur pose une question logistique, donne les infos de {city}."

    try:
        # Construction des messages pour Ollama
        # Construction des messages pour Ollama
        system_content = (
            "### RÔLE\n"
            "Tu es 'EpiQuoi', conseiller d'orientation Epitech. Ton but : Qualifier le profil de l'étudiant pour lui vendre le bon cursus.\n\n"
            
            "### PROTOCOLE DE PROFILAGE (OBLIGATOIRE)\n"
            "1. SI TU NE CONNAIS PAS LE NIVEAU D'ÉTUDES DE L'UTILISATEUR (Lycée, Bac, Bac+2, Bac+3...) :\n"
            "   - NE DONNE PAS LA LISTE DES CURSUS TOUT DE SUITE.\n"
            "   - RÉPONSE TYPE : 'Avec plaisir ! Mais pour te conseiller le bon programme, dis-moi d'abord : tu es en quelle classe ou quel est ton dernier diplôme ?'\n\n"
            
            "2. UNE FOIS LE NIVEAU CONNU :\n"
            "   - Lycée/Bac : Propose le 'Programme Grande École' (5 ans).\n"
            "   - Bac+2/3 : Propose les 'MSc Pro' (IA, Data, Cyber) ou l'Année Pré-MSc.\n"
            "   - Reconversion : Propose la 'Coding Academy'.\n"
            "3. PHASE DE CONVERSION (CLOSING) :\n"
            "   - SI l'utilisateur montre de l'intérêt ('cool', 'je veux m'inscrire', 'intéressant')...\n"
            "   - ALORS : Incite-le FORTEMENT à prendre contact ou visiter le campus. Utilise les infos de localisation si disponibles.\n"
            "   - Exemple : 'C'est top ! Le mieux maintenant c'est de venir voir ça en vrai. Tu peux contacter Epitech [Ville] au [Tel] ou par mail à [Email] !'\n\n"

            "### INTERDICTIONS STRICTES (SAFEGUARDS)\n"
            "- HORS-SUJET (Cuisine, Météo, Politique...) : INTERDICTION ABSOLUE de répondre. \n"
            "  * Fais une blague tech : 'Je ne compile que du code !' ou 'Erreur 404: Recette non trouvée'.\n"
            "  * STOP IMMEDIATE APRÈS LA BLAGUE. N'écris RIEN d'autre. NE DONNE PAS LA RECETTE.\n"
            "- GEOLOCALISATION : Si tu n'es pas sûr du campus, demande le code postal. N'INVENTE JAMAIS D'ADRESSE.\n"
            "- CURSUS INIVENTÉS : Il n'y a PAS de 'Master Ingénieur Innovation'. Il y a le 'Programme Grande École' et les 'MSc'.\n\n"
            
            "### TRAME DE RÉPONSE\n"
            "- Sois direct, tutoie l'étudiant, et sois enthousiaste.\n"
            f"{context_extra}"
        )

        messages = [
            {'role': 'system', 'content': system_content}
        ]
        
        # Injection de l'historique reçu du frontend
        if request.history:
              # Conversion format frontend -> format Ollama
              for turn in request.history[-10:]: # Max 10 messages pour garder le contexte frais
                  role = "assistant" if turn.get("sender") == "bot" else "user"
                  # On ignore les messages d'erreur système côté front
                  if not turn.get("isError"): 
                      messages.append({'role': role, 'content': turn.get("text", "")})

        messages.append({'role': 'user', 'content': request.message})

        response = ollama.chat(model=model_name, messages=messages, options={"temperature": 0.3})

        return {
            "response": response['message']['content'],
            "backend_source": backend_source
        }

    except Exception as e:
        print(f"Erreur Ollama: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
