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
    "Barcelone": {"zip": "08005", "addr": "Carrer de Joan Miró, 21, 08005 Barcelona, Espagne", "coords": (41.3909, 2.1940), "email": "barcelona@epitech.eu", "phone": "+34 937 97 88 14"},
    "Berlin": {"zip": "10623", "addr": "Fasanenstraße 86, 10623 Berlin, Allemagne", "coords": (52.5084, 13.3293), "email": "berlin@epitech.eu", "phone": "+49 30 982 892 41"},
    "Bruxelles": {"zip": "1000", "addr": "Rue Royale 196, 1000 Bruxelles, Belgique", "coords": (50.8523, 4.3651), "email": "brussels@epitech.eu", "phone": "+32 2 315 22 82"},
    "Cotonou": {"zip": "00000", "addr": "Campus Sèmè One, Cotonou, Bénin", "coords": (6.3653, 2.4183), "email": "cotonou@epitech.eu", "phone": "+229 69 07 89 02"},
}

CITY_ALIASES = {
    "barcelona": "Barcelone",
    "barna": "Barcelone",
    "brussels": "Bruxelles",
    "brussel": "Bruxelles",
    "berlim": "Berlin",
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
        
        user_label = data['features'][0]['properties'].get('label', 'Localisation inconnue')
        user_context = data['features'][0]['properties'].get('context', '')
        user_detected_info = f"{user_label} ({user_context})"

        # 2. Trouver le campus le plus proche (Distance Haversine)
        min_dist = float('inf')
        nearest = None
        
        for city, info in CAMPUSES.items():
            camp_lat, camp_lon = info['coords']
            dist = haversine_distance(user_lat, user_lon, camp_lat, camp_lon)
            if dist < min_dist:
                min_dist = dist
                nearest = (city, info)

        if nearest:
             return (nearest[0], nearest[1], int(min_dist), user_detected_info) # (City, Data, Dist, UserInfo)
        
        return None
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

    # Fallback: Si pas de regex location trouvée, on cherche si une ville connue (ou alias) est citée directement
    if not location_query:
        # Check Main Cities
        for known_city in CAMPUSES.keys():
             if known_city.lower() in msg_lower:
                 location_query = known_city
                 break
        # Check Aliases
        if not location_query:
            for alias, target_city in CITY_ALIASES.items():
                if alias in msg_lower:
                    location_query = target_city
                    break

    direct_city_match = None
    if location_query:
        # Check si la location trouvée (via regex ou fallback) est une ville campus connue
        # On normalise pour vérifier
        loc_normalized = location_query.lower()
        
        # 1. Check direct keys
        for known_city in CAMPUSES.keys():
            if known_city.lower() == loc_normalized:
                direct_city_match = known_city
                break
        
        # 2. Check aliases if not found
        if not direct_city_match:
            if loc_normalized in CITY_ALIASES:
                direct_city_match = CITY_ALIASES[loc_normalized]

        if direct_city_match:
             print(f"🔍 Tool Activation: Direct City Match! ({direct_city_match}) - Skipping Geocoder")
             city = direct_city_match
             data = CAMPUSES[city]
             dist_km = 0
             user_detected_info = f"{city} (Détection directe)"
             near_campus = (city, data, dist_km, user_detected_info) # On simule le retour
        else:
             print(f"🔍 Tool Activation: Geocoding API ({location_query})")
             near_campus = await get_nearest_campus(location_query)
             
        if near_campus:
            city, data, dist_km, user_detected_info = near_campus # NEW: Unpacking 4 elements
            
            is_same_city = location_query.lower() in city.lower() or city.lower() in location_query.lower()

            # SI ON EST DANS LA VILLE DU CAMPUS (Distance < 10km ou même ville)
            if is_same_city or dist_km < 10:
                context_extra += (
                    f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                    f"Excellente nouvelle : Epitech est PRÉSENT à {city} !\n"
                    f"Tu PEUX lui donner directement l'adresse : {data['addr']}.\n"
                    f"Contact : {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}\n"
                )
            else:
                 # CAS ELOIGNÉ
                 context_extra += (
                    f"\n\n[INFO SYSTÈME: LOCALISATION]\n"
                    f"L'utilisateur semble être à : '{location_query}' ({user_detected_info}).\n"
                    f"ATTENTION : Pas de campus EXACTEMENT ici. Le plus proche est {city.upper()} ({dist_km} km).\n"
                    f"Propose-lui de contacter {city}.\n"
                    f"Coordonnées de {city}: {data['addr']}.\n"
                    f"Contact {city}: {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}\n"
                 )
            
            if not is_same_city and dist_km > 5: # Si > 5km de différence
                 context_extra += (
                    f"CONTEXTE GEOGRAPHIQUE : L'utilisateur se trouve à {location_query}, où il n'y a PAS de campus Epitech. "
                    f"Le campus le plus proche est celui de {city} (à {dist_km}km). "
                    f"Il faut donc lui proposer de contacter le campus de {city}. "
                    f"Ne pas inventer de campus à {location_query}."
                 )
            
            context_extra += f"\nInfos contact pour {city} : {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}."

    # DEBUG: Voir ce qui est détecté
    if location_query:
        print(f"DEBUG LOCATION: Query='{location_query}' -> Nearest='{city}'")


    try:
        # Construction des messages pour Ollama
        
        # LISTE OFFICIELLE POUR ANTI-HALLUCINATION
        valid_cities_str = ", ".join([c.upper() for c in CAMPUSES.keys()])

        system_content = (
            "### RÔLE\n"
            "Tu es 'EpiQuoi', conseiller d'orientation Epitech. Ton but : Qualifier le profil de l'étudiant.\n\n"
            
            "### LANGUE (IMPORTANT)\n"
            "DETECTE LA LANGUE DE L'UTILISATEUR (Français, Anglais, Espagnol...) ET RÉPONDS DANS LA MÊME LANGUE.\n"
            "C'est primordial pour l'expérience utilisateur.\n\n"
            
            "### VÉRITÉ GÉOGRAPHIQUE (CRITIQUE)\n"
            f"Voici la LISTE EXCLUSIVE des villes où Epitech a un campus : {valid_cities_str}.\n"
            "RÈGLE D'OR : Si l'utilisateur mentionne une ville (ex: Metz, Brest, Tours...) qui n'est PAS dans cette liste :\n"
            "1. TU DOIS DIRE qu'il n'y a pas de campus dans cette ville.\n"
            "2. Propose toujours le campus le plus proche (selon le contexte système).\n"
            "3. N'INVENTE JAMAIS D'ADRESSE ou de téléphone pour une ville hors liste.\n\n"

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

        # FORCER LE CONTEXTE DANS LE DERNIER MESSAGE USER
        # C'est la technique la plus efficace contre les hallucinations : mettre le contexte juste devant la tâche.
        final_user_content = request.message
        if context_extra:
            final_user_content += f"\n\n(Information système : {context_extra})"
        
        # Consigne Langue (Force à la fin)
        final_user_content += "\n\n[INSTRUCTION SYSTÈME ULTIME : RÉPONDS DANS LA MÊME LANGUE QUE LE MESSAGE DE L'UTILISATEUR (Français si User parle FR, Anglais si User parle EN, etc.)]"

        messages.append({'role': 'user', 'content': final_user_content})

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
