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
# NOTE: Pour le dev local, on autorise TOUT (*) et on désactive les credentials pour éviter les conflits.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
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
    "Paris": {"country": "France", "zip": "94270", "addr": "24 rue Pasteur, 94270 Le Kremlin-Bicêtre", "coords": (48.8156, 2.3631), "email": "paris@epitech.eu", "phone": "01 44 08 00 60"},
    "Bordeaux": {"country": "France", "zip": "33000", "addr": "81-89 Rue du Jardin public, 33000 Bordeaux", "coords": (44.8432, -0.5756), "email": "bordeaux@epitech.eu", "phone": "05 64 13 05 84"},
    "Lille": {"country": "France", "zip": "59000", "addr": "5-9 Rue du Palais Rihour, 59000 Lille", "coords": (50.6359, 3.0617), "email": "lille@epitech.eu", "phone": "03 74 09 16 24"},
    "Lyon": {"country": "France", "zip": "69000", "addr": "86 Boulevard Marius Vivier Merle, 69003 Lyon", "coords": (45.7597, 4.8584), "email": "lyon@epitech.eu", "phone": "04 28 29 33 25"},
    "Marseille": {"country": "France", "zip": "13000", "addr": "21 Rue Marc Donadille, 13013 Marseille", "coords": (43.3444, 5.4243), "email": "marseille@epitech.eu", "phone": "04 84 89 13 54"},
    "Montpellier": {"country": "France", "zip": "34000", "addr": "16 Boulevard des Arceaux, 34000 Montpellier", "coords": (43.6095, 3.8687), "email": "montpellier@epitech.eu", "phone": "04 11 93 17 52"},
    "Nantes": {"country": "France", "zip": "44000", "addr": "18 Rue Flandres-Dunkerque, 44000 Nantes", "coords": (47.2156, -1.5552), "email": "nantes@epitech.eu", "phone": "02 85 52 28 71"},
    "Nancy": {"country": "France", "zip": "54000", "addr": "80 Rue Saint-Georges, 54000 Nancy", "coords": (48.6923, 6.1848), "email": "nancy@epitech.eu", "phone": "03 72 47 11 50"},
    "Nice": {"country": "France", "zip": "06000", "addr": "13 Rue Saint-François de Paule, 06300 Nice", "coords": (43.6961, 7.2718), "email": "nice@epitech.eu", "phone": "04 22 13 32 66"},
    "Rennes": {"country": "France", "zip": "35000", "addr": "19 Rue Jean-Marie Huchet, 35000 Rennes", "coords": (48.1130, -1.6738), "email": "rennes@epitech.eu", "phone": "02 57 22 08 54"},
    "Strasbourg": {"country": "France", "zip": "67000", "addr": "4 Rue du Dôme, 67000 Strasbourg", "coords": (48.5831, 7.7479), "email": "strasbourg@epitech.eu", "phone": "03 67 10 28 83"},
    "Toulouse": {"country": "France", "zip": "31000", "addr": "40 Boulevard de la Marquette, 31000 Toulouse", "coords": (43.6125, 1.4287), "email": "toulouse@epitech.eu", "phone": "05 82 95 79 93"},
    "Barcelone": {"country": "Espagne", "zip": "08005", "addr": "Carrer de Joan Miró, 21, 08005 Barcelona, Espagne", "coords": (41.3909, 2.1940), "email": "barcelona@epitech.eu", "phone": "+34 937 97 88 14"},
    "Berlin": {"country": "Allemagne", "zip": "10623", "addr": "Fasanenstraße 86, 10623 Berlin, Allemagne", "coords": (52.5084, 13.3293), "email": "berlin@epitech.eu", "phone": "+49 30 982 892 41"},
    "Bruxelles": {"country": "Belgique", "zip": "1000", "addr": "Rue Royale 196, 1000 Bruxelles, Belgique", "coords": (50.8523, 4.3651), "email": "brussels@epitech.eu", "phone": "+32 2 315 22 82"},
    "Cotonou": {"country": "Benin", "zip": "00000", "addr": "Campus Sèmè One, Cotonou, Bénin", "coords": (6.3653, 2.4183), "email": "cotonou@epitech.eu", "phone": "+229 69 07 89 02"},
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

async def get_nearest_campus(query_zip):
    try:
        user_coords = None
        user_label = "Localisation inconnue"
        user_country_detected = "Inconnu"

        async with httpx.AsyncClient() as client:
            # 1. Tentative API Gouv (France)
            # On utilise query_zip ici
            resp = await client.get(f"https://api-adresse.data.gouv.fr/search/?q={query_zip}&limit=1")
            data = resp.json()

            valid_french_result = False
            if data.get('features'):
                props = data['features'][0]['properties']
                result_type = props.get('type')
                user_city_name = props.get('city', '')
                normalized_query = query_zip.lower().strip()
                
                # Validation anti faux-positifs
                # Si c'est une rue et que le nom de la ville ne contient pas notre recherche
                if not (result_type == 'street' and normalized_query not in user_city_name.lower()):
                     valid_french_result = True
                     user_coords = data['features'][0]['geometry']['coordinates']
                     user_label = props.get('label')
                     user_country_detected = "France"
                else:
                    # Si c'est rejeté comme faux positif (ex: Rue de metz à Nantes), on check si c'est un zip
                    if query_zip.isdigit():
                        # Si c'est un zip, on accepte quand même (c'est rare de taper un zip qui correspond à une rue ailleurs)
                         valid_french_result = True
                         user_coords = data['features'][0]['geometry']['coordinates']
                         user_label = props.get('label')
                         user_country_detected = "France"


            # 2. Si échec France, Tentative OpenStreetMap (Monde)
            if not valid_french_result:
                print(f"🌍 Switching to Nominatim for: {query_zip}")
                headers = {'User-Agent': 'EpiChat/1.0'}
                resp_osm = await client.get(f"https://nominatim.openstreetmap.org/search?q={query_zip}&format=json&limit=1", headers=headers)
                data_osm = resp_osm.json()
                
                if data_osm:
                    user_coords = [float(data_osm[0]['lon']), float(data_osm[0]['lat'])]
                    user_label = data_osm[0]['display_name']
                    # Simplistic country detection from display name
                    if "Germany" in user_label or "Deutschland" in user_label: user_country_detected = "Allemagne"
                    elif "Spain" in user_label or "España" in user_label: user_country_detected = "Espagne"
                    elif "Belgium" in user_label or "Belgique" in user_label: user_country_detected = "Belgique"
                    else: user_country_detected = "Autre"
        
        if not user_coords:
            return None

        user_lon, user_lat = user_coords[0], user_coords[1]
        user_detected_info = f"{user_label} (Pays: {user_country_detected})"

        # 3. Calcul des distances pour TOUS les campus
        # On stocke tout pour trier
        results = []
        for city, info in CAMPUSES.items():
            camp_lat, camp_lon = info['coords']
            dist = haversine_distance(user_lat, user_lon, camp_lat, camp_lon)
            results.append({'city': city, 'dist': int(dist), 'data': info})
        
        # Tri par distance
        results.sort(key=lambda x: x['dist'])

        nearest_overall = results[0]
        
        # Trouver le plus proche DANS LE PAYS de l'utilisateur (si connu)
        nearest_in_country = None
        if user_country_detected and user_country_detected != "Autre":
             nearest_in_country = next((r for r in results if r['data']['country'] == user_country_detected), None)

        return (nearest_overall, nearest_in_country, user_detected_info)

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

    # Détection de langue (Basique)
    user_lang = "fr"
    try:
        from langdetect import detect
        if len(request.message.split()) > 3: # On ne détecte que si le message est assez long
            detected = detect(request.message)
            if detected != 'fr':
                user_lang = detected
                print(f"🌍 Language Detected: {user_lang}")
    except ImportError:
        print("⚠️ Langdetect not installed")
    except Exception as e:
        print(f"⚠️ Lang detection failed: {e}")

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
             
             # Mock structure for direct match
             nearest_overall = {'city': city, 'dist': 0, 'data': data}
             nearest_in_country = nearest_overall
             near_campus = (nearest_overall, nearest_in_country, user_detected_info) 
        else:
             print(f"🔍 Tool Activation: Geocoding API ({location_query})")
             near_campus = await get_nearest_campus(location_query)
             
        if near_campus:
            nearest_overall, nearest_in_country, user_detected_info = near_campus 
            
            # --- FIX: Initialization of variables used later ---
            city = nearest_overall['city']
            data = nearest_overall['data']
            dist_km = nearest_overall['dist']
            # ---------------------------------------------------

            # PAR DÉFAUT : On recommande le plus proche absolu
            rec_city = nearest_overall['city']
            rec_data = nearest_overall['data']
            rec_dist = nearest_overall['dist']
            
            # EXCEPTION GEOPOLITIQUE : Si un campus existe dans le MEME PAYS que l'user, on le priorise
            # sauf si la différence de distance est énorme (ex: > 300km)
            is_national_priority = False
            if nearest_in_country and nearest_in_country['city'] != rec_city:
                 nat_dist = nearest_in_country['dist']
                 # On favorise le national si la distance reste raisonnable par rapport à l'absolu (ex: Absolu 120km FR vs National 140km ES -> Go ES)
                 if nat_dist < (rec_dist + 200): 
                      rec_city = nearest_in_country['city']
                      rec_data = nearest_in_country['data']
                      rec_dist = nat_dist
                      is_national_priority = True

            is_same_city = location_query.lower() in rec_city.lower() or rec_city.lower() in location_query.lower()

            # SI ON EST DANS LA VILLE DU CAMPUS
            if is_same_city or rec_dist < 10:
                context_extra += (
                    f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                    f"Excellente nouvelle : Epitech est PRÉSENT à {rec_city} !\n"
                    f"Adresse : {rec_data['addr']}.\n"
                    f"Contact : {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
                )
            else:
                 # CAS ELOIGNÉ
                 priority_msg = "PREFERENCE NATIONALE" if is_national_priority else "PROXIMITÉ GÉOGRAPHIQUE"
                 context_extra += (
                    f"\n\n[INFO SYSTÈME: LOCALISATION]\n"
                    f"L'utilisateur est à : '{location_query}' ({user_detected_info}).\n"
                    f"Campus recommandé ({priority_msg}) : {rec_city.upper()} ({rec_dist} km).\n"
                 )
                 
                 if is_national_priority:
                     context_extra += f"Note: Le campus absolu le plus proche est {nearest_overall['city']} ({nearest_overall['dist']}km), mais il est dans un autre pays.\n"

                 context_extra += (
                    f"Propose-lui de contacter {rec_city}.\n"
                    f"Coordonnées de {rec_city}: {rec_data['addr']}.\n"
                    f"Contact {rec_city}: {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
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
        debug_city = city if 'city' in locals() else "None"
        print(f"DEBUG LOCATION: Query='{location_query}' -> Nearest='{debug_city}'")


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
        if user_lang != 'fr':
             final_user_content += f"\n\n[CRITICAL: THE USER SPEAKS {user_lang.upper()}. YOU MUST ANSWER IN {user_lang.upper()}. DO NOT SPEAK FRENCH.]"
        else:
             final_user_content += "\n\n[INSTRUCTION SYSTÈME ULTIME : RÉPONDS DANS LA MÊME LANGUE QUE LE MESSAGE DE L'UTILISATEUR]"

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
