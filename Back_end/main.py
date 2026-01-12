from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import os
from dotenv import load_dotenv
import httpx
import math
import asyncio

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

# Fonction Tool pour récupérer les news (ASYNC - non-bloquante)
async def get_epitech_news():
    try:
        scraper_path = os.path.join(os.path.dirname(__file__), "../MCP_Server/epitech_scraper")
        
        # CORRECTION 1 & 2 : On utilise asyncio pour ne pas bloquer
        # et on récupère la sortie standard (stdout) au lieu d'écrire un fichier
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "scrapy", "crawl", "epitech_news", "-O", "-", "-t", "json",
            cwd=scraper_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # On attend la fin sans bloquer le serveur
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"Scrapy Error: {stderr.decode()}")
            return "Désolé, impossible de récupérer les actualités pour le moment."

        # On lit le JSON directement depuis la mémoire (stdout)
        news_data = json.loads(stdout.decode())
            
        formatted_news = "Voici les dernières actualités Epitech récupérées en direct :\n"
        for item in news_data[:3]:
            title = item.get('title', 'Sans titre').strip()
            summary = item.get('summary', '').strip()
            link = item.get('link', '#')
            formatted_news += f"- {title}: {summary} (Source: {link})\n"
            
        return formatted_news

    except Exception as e:
        print(f"Erreur News: {str(e)}")
        return "Erreur technique lors de la récupération des news."

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


    # Détection de langue (Améliorée - Anti faux-positifs)
    user_lang = "fr"
    supported_langs = {"fr", "en", "es", "de"}  # Français, Anglais, Espagnol, Allemand
    
    try:
        from langdetect import detect
        # Seuil plus strict : au moins 8 mots pour éviter les faux positifs ("ca a l'air" → catalan)
        if len(request.message.split()) >= 8:
            detected = detect(request.message)
            # Ne changer que si la langue détectée est supportée ET différente du français
            if detected in supported_langs and detected != 'fr':
                user_lang = detected
                print(f"🌍 Language Detected: {user_lang}")
            else:
                print(f"🌍 Language Detected: {detected} (ignored, defaulting to French)")
    except ImportError:
        print("⚠️ Langdetect not installed")
    except Exception as e:
        print(f"⚠️ Lang detection failed: {e}")

    # Tool 1: News Scraper
    if any(k in msg_lower for k in keywords_news) and "epitech" in msg_lower:
        print("🔍 Tool Activation: Scraper Epitech News")
        news_info = await get_epitech_news()  # AWAIT pour ne pas bloquer
        context_extra += f"\n\n[SYSTÈME: DONNÉES LIVE INJECTÉES]\n{news_info}\nUtilise ces informations pour répondre."
        backend_source += " + Scraper"

    # Tool 2: Campus Finder (CORRECTION #3 - Regex améliorée + Filtrage contextuel)
    import re
    location_query = None
    
    # SAFEGUARD : Ne pas déclencher l'outil si l'utilisateur parle juste d'Epitech en général
    # ou exprime simplement une réaction
    non_location_keywords = ["méthodologie", "methodologie", "pédagogie", "pedagogie", "programme", 
                             "cursus", "formation", "apprentissage", "méthode", "enseignement",
                             "apprentissage", "étude", "cours", "diplome", "diplôme",
                             # Réactions positives/négatives (pas de contexte géographique)
                             "intéressant", "interessant", "cool", "sympa", "super", "génial",
                             "l'air", "lair", "semble", "parait", "paraît"]
    
    # Mots à rejeter si capturés par la regex (faux positifs courants)
    invalid_location_words = {"l", "la", "le", "les", "un", "une", "des", "air", "lair", "l'air",
                               "bien", "mal", "bon", "bonne", "très", "trop", "peu", "plus",
                               "être", "etre", "avoir", "fait", "faire", "dit", "dire",
                               "intéressant", "interessant", "cool", "sympa", "super"}
    
    is_general_epitech_question = any(kw in msg_lower for kw in non_location_keywords)
    
    if not is_general_epitech_question:  # Ne chercher une localisation QUE si contexte géographique
        # 1. Regex Code Postal (5 chiffres)
        zip_match = re.search(r'\b\d{5}\b', request.message)
        if zip_match:
            location_query = zip_match.group(0)
        else:
            # 2. Regex Ville STRICTE - Exige un verbe de localisation AVANT
            # "habite à Lyon", "suis de Metz", "viens de Bordeaux", "vis à Lille"
            city_match = re.search(r'(?i)\b(?:habite|vis|viens|suis)\s+(?:à|a|de|d\')\s*([a-zA-Z\u00C0-\u00FF]{3,})\b', request.message)
            if city_match:
                candidate = city_match.group(1).strip().lower()
                # Valider que ce n'est pas un faux positif
                if candidate not in invalid_location_words:
                    location_query = city_match.group(1).strip()
            
            if not location_query:
                # 3. Cas spécifique : "campus [ville]" ou "Epitech [ville]" mais SEULEMENT si [ville] est connue
                campus_city_match = re.search(r'(?i)(?:campus|epitech)\s+([a-zA-Z\u00C0-\u00FF\-]+)', request.message)
                if campus_city_match:
                    candidate = campus_city_match.group(1).strip()
                    # Vérifier que c'est un nom de ville connu (pas "methodologie")
                    if candidate.lower() in [c.lower() for c in CAMPUSES.keys()] or candidate.lower() in CITY_ALIASES:
                        location_query = candidate
                
                # 4. ULTIME SECOURS : Ville connue mentionnée directement
                if not location_query:
                    for known_city in CAMPUSES.keys():
                        # Check avec boundary pour éviter "Nantes" dans "enseignantes"
                        if re.search(rf'\b{re.escape(known_city.lower())}\b', msg_lower):
                            location_query = known_city
                            break
                    
                    # 5. Check Aliases si toujours rien
                    if not location_query:
                        for alias, target_city in CITY_ALIASES.items():
                            if re.search(rf'\b{re.escape(alias)}\b', msg_lower):
                                location_query = target_city
                                break

    # CORRECTION #2 - Variables thread-safe (pas de modification de CAMPUSES global)
    city = "Inconnu"
    data = {}
    dist_km = 0
    
    if location_query:
        # Check si la location trouvée est un nom de ville campus exact (skip geocoding)
        direct_city_match = None
        loc_normalized = location_query.lower()
        
        for known_city in CAMPUSES.keys():
            if known_city.lower() == loc_normalized:
                direct_city_match = known_city
                break
        
        if not direct_city_match and loc_normalized in CITY_ALIASES:
            direct_city_match = CITY_ALIASES[loc_normalized]

        if direct_city_match:
            print(f"🔍 Direct City Match: {direct_city_match}")
            city = direct_city_match
            data = CAMPUSES[city]
            dist_km = 0
            
            context_extra += (
                f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                f"Epitech est à {city.upper()} !\n"
                f"Adresse : {data['addr']}.\n"
                f"Contact : {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}\n"
            )
        else:
            # Geocoding API nécessaire
            print(f"🔍 Geocoding API: {location_query}")
            geo_result = await get_nearest_campus(location_query)
            
            if geo_result:
                nearest_overall, nearest_in_country, user_detected_info = geo_result
                
                city = nearest_overall['city']
                data = nearest_overall['data']
                dist_km = nearest_overall['dist']
                
                # Logique de recommandation (prioriser le pays si pertinent)
                rec_city = city
                rec_data = data
                rec_dist = dist_km
                is_national_priority = False
                
                if nearest_in_country and nearest_in_country['city'] != rec_city:
                    nat_dist = nearest_in_country['dist']
                    if nat_dist < (rec_dist + 200):
                        rec_city = nearest_in_country['city']
                        rec_data = nearest_in_country['data']
                        rec_dist = nat_dist
                        is_national_priority = True
                
                is_same_city = location_query.lower() in rec_city.lower() or rec_city.lower() in location_query.lower()
                
                if is_same_city or rec_dist < 10:
                    context_extra += (
                        f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                        f"Epitech est à {rec_city.upper()} !\n"
                        f"Adresse : {rec_data['addr']}.\n"
                        f"Contact : {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
                    )
                else:
                    priority_msg = "PRÉFÉRENCE NATIONALE" if is_national_priority else "PROXIMITÉ"
                    context_extra += (
                        f"\n\n[INFO SYSTÈME: LOCALISATION]\n"
                        f"Localisation détectée : '{location_query}' ({user_detected_info}).\n"
                        f"Campus recommandé ({priority_msg}) : {rec_city.upper()} ({rec_dist} km).\n"
                        f"Adresse : {rec_data['addr']}.\n"
                        f"Contact : {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
                    )
                    
                    if not is_same_city and rec_dist > 5:
                        context_extra += (
                            f"\n⚠️ GARDE-FOU : Il n'y a PAS de campus à {location_query}. "
                            f"Le plus proche est {rec_city} ({rec_dist}km). "
                            f"N'invente JAMAIS d'adresse pour {location_query}.\n"
                        )

    # DEBUG: Voir ce qui est détecté
    if location_query:
        debug_city = city if 'city' in locals() else "None"
        print(f"DEBUG LOCATION: Query='{location_query}' -> Nearest='{debug_city}'")


    try:
        # Construction des messages pour Ollama
        
        # LISTE OFFICIELLE POUR ANTI-HALLUCINATION
        valid_cities_str = ", ".join([c.upper() for c in CAMPUSES.keys()])

        # --- DETECTION AUTOMATIQUE DU NIVEAU D'ÉTUDES ---
        detected_level = None
        level_keywords = {
            "bac": ["bac ", "bac+0", "baccalauréat", "terminale", "stmg", "sti2d", "stl", "st2s", "es", "s ", "l ", "bac s", "bac es", "bac l", "bac pro", "bac techno"],
            "bac+2": ["bac+2", "bts", "dut", "deug", "l2", "licence 2"],
            "bac+3": ["bac+3", "licence", "bachelor", "l3", "licence 3"],
            "bac+4": ["bac+4", "m1", "master 1", "maîtrise"],
            "bac+5": ["bac+5", "m2", "master 2", "ingénieur", "diplôme d'ingénieur"],
            "reconversion": ["reconversion", "changement de carrière", "réorientation", "salarié", "demandeur d'emploi"],
            "lycee": ["lycée", "lyceen", "seconde", "première", "1ère", "2nde"]
        }
        
        msg_check = msg_lower
        for level, keywords in level_keywords.items():
            for kw in keywords:
                if kw in msg_check:
                    detected_level = level
                    print(f"🎓 Niveau d'études détecté: {level} (keyword: '{kw}')")
                    break
            if detected_level:
                break
        
        # Construction du prompt avec info de niveau si détecté
        level_context = ""
        if detected_level:
            if detected_level in ["bac", "lycee"]:
                level_context = (
                    "\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = BAC/LYCÉE]\n"
                    "L'utilisateur a mentionné avoir le BAC ou être au lycée. "
                    "NE LUI DEMANDE PAS SON NIVEAU, tu le connais déjà ! "
                    "Propose-lui directement le 'Programme Grande École' (5 ans, post-bac) !\n"
                )
            elif detected_level in ["bac+2", "bac+3"]:
                level_context = (
                    f"\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = {detected_level.upper()}]\n"
                    "L'utilisateur a un Bac+2 ou Bac+3. "
                    "Propose-lui les 'MSc Pro' (IA, Data, Cybersécurité) ou l'Année Pré-MSc !\n"
                )
            elif detected_level == "reconversion":
                level_context = (
                    "\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = RECONVERSION]\n"
                    "L'utilisateur est en reconversion professionnelle. "
                    "Propose-lui la 'Coding Academy' (bootcamp intensif) !\n"
                )

        # CORRECTION #1 - ANTI-HALLUCINATION : Injecter la liste TOUJOURS, pas seulement si l'outil est déclenché
        system_content = (
            "### RÔLE\n"
            "Tu es 'EpiQuoi', conseiller d'orientation Epitech. Ton but : Qualifier le profil de l'étudiant.\n\n"
            
            "### LANGUE (IMPORTANT)\n"
            "DETECTE LA LANGUE DE L'UTILISATEUR (Français, Anglais, Espagnol...) ET RÉPONDS DANS LA MÊME LANGUE.\n"
            "C'est primordial pour l'expérience utilisateur.\n\n"
            
            "### ⚠️ VÉRITÉ GÉOGRAPHIQUE - RÈGLE ABSOLUE (CRITIQUE) ⚠️\n"
            f"LISTE EXCLUSIVE DES CAMPUS EPITECH : {valid_cities_str}.\n\n"
            "RÈGLES IMPÉRATIVES :\n"
            "1. Si l'utilisateur demande une adresse/infos pour une ville NON listée ci-dessus (ex: Metz, Brest, Rouen, Tours...) :\n"
            "   → TU DOIS REFUSER. Dis clairement : 'Il n'y a pas de campus Epitech à [Ville]'.\n"
            "   → Propose le campus le plus proche (si disponible dans le contexte système).\n"
            "2. N'INVENTE JAMAIS d'adresse, de téléphone, ou d'email pour une ville hors liste.\n"
            "3. Si tu n'es pas sûr, demande le code postal de l'utilisateur.\n\n"

            "### PROTOCOLE DE PROFILAGE (CRITIQUE)\n"
            "⚠️ AVANT DE DEMANDER LE NIVEAU D'ÉTUDES, VÉRIFIE SI L'UTILISATEUR L'A DÉJÀ MENTIONNÉ !\n"
            "Mots-clés : 'bac', 'stmg', 'sti2d', 'licence', 'bts', 'dut', 'master', 'reconversion', 'lycée', 'terminale'...\n"
            "SI DÉTECTÉ → Passe DIRECTEMENT aux recommandations !\n\n"
            
            "RECOMMANDATIONS PAR NIVEAU :\n"
            "   - Lycée/Bac (STMG, STI2D, Bac Pro...) → 'Programme Grande École' (5 ans post-bac).\n"
            "   - Bac+2/3 (BTS, DUT, Licence) → 'MSc Pro' (IA, Data, Cyber) ou 'Année Pré-MSc'.\n"
            "   - Reconversion → 'Coding Academy'.\n\n"
            
            "### PHASE DE CONVERSION (IMPORTANT)\n"
            "SIGNAUX D'INTÉRÊT à détecter : 'intéressant', 'cool', 'sympa', 'ça a l'air', 'je veux', 'inscription'...\n"
            "SI SIGNAL DÉTECTÉ :\n"
            "   1. Confirme son intérêt (ex: 'Content que ça te plaise !').\n"
            "   2. Propose NATURELLEMENT de passer à l'étape suivante (contact, visite, candidature).\n"
            "   3. Si tu as des infos de localisation (contexte système), utilise-les pour donner le contact du campus proche.\n"
            "   4. RESTE NATUREL : pas de forcing commercial, juste helpful.\n\n"

            "### INTERDICTIONS STRICTES\n"
            "- HORS-SUJET : Blague tech + STOP. Ne donne AUCUNE info sur le sujet.\n"
            "- Cursus valides uniquement : 'Programme Grande École', 'MSc Pro', 'Coding Academy'.\n\n"
            
            "### TRAME\n"
            "- Direct, tutoiement, enthousiaste.\n"
            "- Ne répète pas ce que l'utilisateur a déjà dit.\n"
            "- TOUJOURS répondre dans la langue de l'utilisateur.\n"
            f"{level_context}"
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
