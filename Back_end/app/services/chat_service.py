"""Service for chat interactions with Ollama."""

import logging
import re
from typing import List, Dict, Optional, Tuple

import ollama
import os

from app.config import settings

# Configure Ollama client URL if specified
# Ollama uses OLLAMA_HOST environment variable (format: host:port)
if settings.ollama_url:
    # Extract host:port from URL (e.g., http://localhost:11434 -> localhost:11434)
    url_parts = settings.ollama_url.replace("http://", "").replace("https://", "")
    os.environ["OLLAMA_HOST"] = url_parts
from app.exceptions import OllamaError
from app.models.schemas import ChatRequest, MessageHistory
from app.services.news_service import NewsService
from app.services.campus_service import CampusService
from app.services.geocoding_service import GeocodingService
from app.utils.campus_data import CAMPUSES, CITY_ALIASES, format_campus_list
from app.utils.language_detection import detect_language

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions."""

    def __init__(self):
        """Initialize chat service with dependencies."""
        self.news_service = NewsService()
        self.campus_service = CampusService()
        self.geocoding_service = GeocodingService()

    # Keywords for intent detection
    NEWS_KEYWORDS = ["news", "actualité", "actu", "nouveauté", "événement"]
    
    NON_LOCATION_KEYWORDS = [
        "méthodologie", "methodologie", "pédagogie", "pedagogie", "programme",
        "cursus", "formation", "apprentissage", "méthode", "enseignement",
        "étude", "cours", "diplome", "diplôme",
        "intéressant", "interessant", "cool", "sympa", "super", "génial",
        "l'air", "lair", "semble", "parait", "paraît"
    ]
    
    INVALID_LOCATION_WORDS = {
        "l", "la", "le", "les", "un", "une", "des", "air", "lair", "l'air",
        "bien", "mal", "bon", "bonne", "très", "trop", "peu", "plus",
        "être", "etre", "avoir", "fait", "faire", "dit", "dire",
        "intéressant", "interessant", "cool", "sympa", "super"
    }
    
    LEVEL_KEYWORDS = {
        "bac": [
            "bac ", "bac+0", "baccalauréat", "terminale", "stmg", "sti2d",
            "stl", "st2s", "es", "s ", "l ", "bac s", "bac es", "bac l",
            "bac pro", "bac techno"
        ],
        "bac+2": ["bac+2", "bts", "dut", "deug", "l2", "licence 2"],
        "bac+3": ["bac+3", "licence", "bachelor", "l3", "licence 3"],
        "bac+4": ["bac+4", "m1", "master 1", "maîtrise"],
        "bac+5": ["bac+5", "m2", "master 2", "ingénieur", "diplôme d'ingénieur"],
        "reconversion": [
            "reconversion", "changement de carrière", "réorientation",
            "salarié", "demandeur d'emploi"
        ],
        "lycee": ["lycée", "lyceen", "seconde", "première", "1ère", "2nde"]
    }

    async def process_chat(self, request: ChatRequest) -> Dict[str, str]:
        """
        Process a chat request and return AI response.
        
        Args:
            request: Chat request with message and history
        
        Returns:
            Dictionary with response and backend_source
        
        Raises:
            OllamaError: If Ollama API fails
        """
        print("=" * 60)
        print(f"📨 NOUVELLE REQUÊTE REÇUE")
        print(f"   Message: {request.message[:100]}{'...' if len(request.message) > 100 else ''}")
        print(f"   Historique: {len(request.history)} messages")
        print("=" * 60)
        
        try:
            # Detect language
            print("🔍 [1/6] Détection de la langue...")
            user_lang = detect_language(
                request.message,
                min_words=settings.min_words_for_lang_detection
            )
            if user_lang != "fr":
                logger.info(f"Language detected: {user_lang}")
                print(f"   ✓ Langue détectée: {user_lang}")
            else:
                print(f"   ✓ Langue par défaut: français")

            # Build context from tools
            context_extra = ""
            backend_source = f"Ollama Local ({settings.ollama_model})"
            msg_lower = request.message.lower()

            # Tool 1: News Scraper
            print("🔍 [2/6] Vérification si scraper NEWS nécessaire...")
            if self._should_fetch_news(msg_lower):
                print("   ⚡ SCRAPER NEWS ACTIVÉ - Démarrage...")
                logger.info("Tool Activation: Scraper Epitech News")
                news_info = await self.news_service.get_epitech_news()
                print("   ✓ Scraping news terminé avec succès")
                context_extra += (
                    f"\n\n[SYSTÈME: DONNÉES LIVE INJECTÉES]\n"
                    f"{news_info}\nUtilise ces informations pour répondre."
                )
                backend_source += " + Scraper News"
            else:
                print("   → Pas de scraper news nécessaire")

            # Tool 1.5: Campus Scraper (Live)
            print("🔍 [2.5/6] Vérification demande scraping campus...")
            if self._should_fetch_campus_data(msg_lower):
                print("   ⚡ SCRAPER CAMPUS ACTIVÉ - Démarrage...")
                logger.info("Tool Activation: Scraper Campus")
                campus_data = await self.campus_service.get_campus_info()
                
                if campus_data:
                    # Vérifier si c'est une liste ou un dict avec erreur
                    if isinstance(campus_data, list):
                        print(f"   ✓ Scraping campus terminé : {len(campus_data)} campus détectés par le scraper")
                    else:
                        print(f"   ⚠️ Format de données inattendu : {type(campus_data)}")
                    
                    # Optimize data to prevent context overflow (OOM)
                    optimized_data = self._optimize_campus_data(campus_data)
                    print(f"   ✓ Données optimisées : {len(optimized_data)} campus conservés après filtrage")
                    
                    # Convert to text to save tokens (JSON is too heavy)
                    campus_text = self._format_campus_to_text(optimized_data)
                    
                    total_campus = len(optimized_data)
                    context_extra += (
                        f"\n\n[SYSTÈME: DONNÉES CAMPUS LIVE - {total_campus} CAMPUS TROUVÉS]\n"
                        f"⚠️ IMPORTANT : Il y a EXACTEMENT {total_campus} campus dans cette liste. "
                        f"Tu DOIS tous les mentionner si on te demande de lister les campus.\n\n"
                        f"Liste complète des campus ({total_campus}) :\n"
                        f"{campus_text}\n\n"
                        f"Si on te demande combien il y a de campus, réponds : {total_campus}. "
                        f"Si on te demande de les lister, cite TOUS les {total_campus} campus de la liste ci-dessus."
                    )
                    backend_source += " + Scraper Campus"
                else:
                    print("   ⚠️ Échec du scraping campus")
            else:
                print("   → Pas de scraping campus demandé")

            # Tool 2: Campus Finder
            print("🔍 [3/6] Détection de localisation...")
            location_context = await self._process_location_detection(
                request.message, msg_lower
            )
            if location_context:
                print("   ✓ Localisation détectée et traitée")
                context_extra += location_context
            else:
                print("   → Aucune localisation détectée")

            # Detect study level
            print("🔍 [4/6] Détection du niveau d'études...")
            detected_level = self._detect_study_level(request.message, request.history)
            if detected_level:
                print(f"   ✓ Niveau détecté: {detected_level}")
            else:
                print("   → Niveau non détecté")
            level_context = self._build_level_context(detected_level)

            # Build system prompt
            print("🔍 [5/6] Construction du prompt système...")
            system_content = self._build_system_prompt(level_context)
            print("   ✓ Prompt système construit")

            # Build messages for Ollama
            print("🔍 [6/6] Préparation des messages pour Ollama...")
            messages = self._build_messages(
                system_content,
                request.message,
                request.history,
                context_extra,
                user_lang
            )
            print(f"   ✓ {len(messages)} messages préparés")

            # Call Ollama with timeout and resource limits
            print(f"\n🤖 APPEL À OLLAMA...")
            print(f"   Modèle: {settings.ollama_model}")
            print(f"   Timeout: {settings.ollama_timeout}s")
            try:
                import asyncio
                import time
                start_time = time.time()
                
                # Wrap synchronous ollama.chat in a thread to prevent blocking
                def call_ollama():
                    return ollama.chat(
                        model=settings.ollama_model,
                        messages=messages,
                        options={
                            "temperature": settings.ollama_temperature,
                            "num_ctx": 2048,  # Limite le contexte pour économiser la mémoire
                            "num_predict": 512,  # Limite la longueur de la réponse
                        }
                    )
                
                # Use async with timeout to prevent system freeze
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, call_ollama),
                    timeout=settings.ollama_timeout
                )
                elapsed_time = time.time() - start_time
                response_length = len(response['message']['content'])
                print(f"   ✓ Réponse reçue en {elapsed_time:.2f}s ({response_length} caractères)")
            except asyncio.TimeoutError:
                logger.error(f"Ollama request timeout after {settings.ollama_timeout}s")
                raise OllamaError(
                    f"La requête a pris trop de temps (>{settings.ollama_timeout}s). "
                    "Essayez un modèle plus léger (llama3.2:1b) ou réduisez la longueur du message."
                )
            except Exception as ollama_error:
                error_msg = str(ollama_error)
                logger.error(f"Ollama connection error: {error_msg}")
                
                # Check if it's a connection error
                if "connection" in error_msg.lower() or "connect" in error_msg.lower():
                    raise OllamaError(
                        "Ollama n'est pas en cours d'exécution. "
                        "Veuillez démarrer Ollama avec la commande : ollama serve"
                    )
                else:
                    raise OllamaError(f"Erreur Ollama : {error_msg}")

            print("=" * 60)
            print("✅ REQUÊTE TRAITÉE AVEC SUCCÈS")
            print(f"   Source: {backend_source}")
            print("=" * 60 + "\n")
            
            return {
                "response": response['message']['content'],
                "backend_source": backend_source
            }

        except OllamaError:
            # Re-raise Ollama errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat service: {e}")
            raise OllamaError(f"Failed to process chat: {str(e)}")

    def _format_campus_to_text(self, data: List[Dict]) -> str:
        """Format optimized campus data into a compact text list."""
        lines = []
        for idx, c in enumerate(data, 1):
            ville = c['ville'].upper()
            pays = c['pays']
            forms = ", ".join(c['formations'][:3]) if c['formations'] else "Toutes formations"  # Limiter à 3 formations max
            if len(c['formations']) > 3:
                forms += f" (+{len(c['formations']) - 3} autres)"
            lines.append(f"{idx}. {ville} ({pays}) : {forms}")
        return "\n".join(lines)

    def _optimize_campus_data(self, data: List[Dict]) -> List[Dict]:
        """Optimize and filter campus data to reduce token usage."""
        optimized = []
        if not isinstance(data, list):
            return []

        for campus in data:
            if not isinstance(campus, dict): continue
            
            # Filter out error messages if any
            if "error" in campus: continue

            # Simple filtered object
            opt_campus = {
                "ville": campus.get("ville"),
                "pays": campus.get("pays"),
                "formations": []
            }
            
            # Filter formations
            raw_formations = campus.get("formations_disponibles", [])
            seen_names = set()
            
            for fmt in raw_formations:
                if not isinstance(fmt, dict): continue
                name = fmt.get("nom", "")
                name_lower = name.lower()
                
                # Filter out irrelevant marketing/contact titles (Noise reduction)
                if any(bad in name_lower for bad in [
                    "où étudier", "plan d’accès", "choisir l’école", "contact", 
                    "informations", "télécharger", "brochure", "plus qu’une école",
                    "nos formations", "nos campus"
                ]):
                    continue
                    
                # Keep relevant academic programs
                if any(k in name_lower for k in ["programme", "bachelor", "master", "msc", "coding", "w@c", "web@cadémie", "bootcamp", "pge", "grande ecole", "grande école"]):
                    # Deduplicate
                    if name in seen_names: continue
                    seen_names.add(name)
                    opt_campus["formations"].append(name)
            
            # Add to list if valid location (on exclut les faux "campus" génériques type 'Apres Bac')
            ville_val = opt_campus["ville"]
            if ville_val and ville_val.lower() not in {"apres bac", "après bac"}:
                optimized.append(opt_campus)
                 
        return optimized

    def _should_fetch_news(self, msg_lower: str) -> bool:
        """Check if news should be fetched based on message content."""
        return (
            any(k in msg_lower for k in self.NEWS_KEYWORDS)
            and "epitech" in msg_lower
            and "epitech" in msg_lower
        )

    def _should_fetch_campus_data(self, msg_lower: str) -> bool:
        """Check if campus scraping should be triggered."""
        # 1. Explicit scraping request
        if "scraper" in msg_lower or "scraping" in msg_lower:
            return True

        # 2. Keywords related to location/campuses
        topic_keywords = ["campus", "école", "ecole", "ville", "implantation", "site", "formations"]
        if not any(k in msg_lower for k in topic_keywords):
            return False

        # 3. Action keywords or context
        # "cite", "liste", "quelles" allow matching "Cite moi...", "Liste les...", "Quelles sont..."
        action_keywords = [
            "epitech", "lister", "liste", "cite", "citer", "donne", "donner",
            "voir", "montre", "montrer", "quels", "quelles", "quel", "quelle",
            "ou", "où", "trouver", "sont", "est", "il y a"
        ]
        return any(k in msg_lower for k in action_keywords)

    async def _process_location_detection(
        self, message: str, msg_lower: str
    ) -> Optional[str]:
        """
        Process location detection and return context string.
        
        Returns:
            Context string to add to prompt, or None
        """
        # Check if this is a general Epitech question (not location-related)
        is_general_question = any(
            kw in msg_lower for kw in self.NON_LOCATION_KEYWORDS
        )

        if is_general_question:
            return None

        # Extract location query
        location_query = self._extract_location_query(message, msg_lower)

        if not location_query:
            return None

        logger.info(f"Location query detected: {location_query}")

        # Check for direct city match
        direct_city_match = self._find_direct_city_match(location_query)

        if direct_city_match:
            logger.info(f"Direct city match: {direct_city_match}")
            city = direct_city_match
            data = CAMPUSES[city]
            return (
                f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                f"Epitech est à {city.upper()} !\n"
                f"Adresse : {data['addr']}.\n"
                f"Contact : {data.get('email', 'N/A')} | {data.get('phone', 'N/A')}\n"
            )

        # Use geocoding API
        logger.info(f"Geocoding API: {location_query}")
        geo_result = await self.geocoding_service.get_nearest_campus(location_query)

        if not geo_result:
            return None

        nearest_overall, nearest_in_country, user_detected_info = geo_result

        city = nearest_overall['city']
        data = nearest_overall['data']
        dist_km = nearest_overall['dist']

        # Recommendation logic (prioritize country if relevant)
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

        is_same_city = (
            location_query.lower() in rec_city.lower()
            or rec_city.lower() in location_query.lower()
        )

        if is_same_city or rec_dist < 10:
            return (
                f"\n\n[INFO SYSTÈME: CAMPUS PRÉSENT !]\n"
                f"Epitech est à {rec_city.upper()} !\n"
                f"Adresse : {rec_data['addr']}.\n"
                f"Contact : {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
            )
        else:
            priority_msg = (
                "PRÉFÉRENCE NATIONALE" if is_national_priority else "PROXIMITÉ"
            )
            context = (
                f"\n\n[INFO SYSTÈME: LOCALISATION]\n"
                f"Localisation détectée : '{location_query}' ({user_detected_info}).\n"
                f"Campus recommandé ({priority_msg}) : {rec_city.upper()} ({rec_dist} km).\n"
                f"Adresse : {rec_data['addr']}.\n"
                f"Contact : {rec_data.get('email', 'N/A')} | {rec_data.get('phone', 'N/A')}\n"
            )

            if not is_same_city and rec_dist > 5:
                context += (
                    f"\n⚠️ GARDE-FOU : Il n'y a PAS de campus à {location_query}. "
                    f"Le plus proche est {rec_city} ({rec_dist}km). "
                    f"N'invente JAMAIS d'adresse pour {location_query}.\n"
                )

            return context

    def _extract_location_query(self, message: str, msg_lower: str) -> Optional[str]:
        """Extract location query from message using regex patterns."""
        # 1. Zip code (5 digits)
        zip_match = re.search(r'\b\d{5}\b', message)
        if zip_match:
            return zip_match.group(0)

        # 2. City with location verb
        city_match = re.search(
            r'(?i)\b(?:habite|vis|viens|suis)\s+(?:à|a|de|d\')\s*([a-zA-Z\u00C0-\u00FF]{3,})\b',
            message
        )
        if city_match:
            candidate = city_match.group(1).strip().lower()
            if candidate not in self.INVALID_LOCATION_WORDS:
                return city_match.group(1).strip()

        # 3. "campus [ville]" or "Epitech [ville]"
        campus_city_match = re.search(
            r'(?i)(?:campus|epitech)\s+([a-zA-Z\u00C0-\u00FF\-]+)',
            message
        )
        if campus_city_match:
            candidate = campus_city_match.group(1).strip()
            if (
                candidate.lower() in [c.lower() for c in CAMPUSES.keys()]
                or candidate.lower() in CITY_ALIASES
            ):
                return candidate

        # 4. Known city mentioned directly
        for known_city in CAMPUSES.keys():
            if re.search(rf'\b{re.escape(known_city.lower())}\b', msg_lower):
                return known_city

        # 5. Check aliases
        for alias, target_city in CITY_ALIASES.items():
            if re.search(rf'\b{re.escape(alias)}\b', msg_lower):
                return target_city

        return None

    def _find_direct_city_match(self, location_query: str) -> Optional[str]:
        """Find direct city match without geocoding."""
        loc_normalized = location_query.lower()

        for known_city in CAMPUSES.keys():
            if known_city.lower() == loc_normalized:
                return known_city

        if loc_normalized in CITY_ALIASES:
            return CITY_ALIASES[loc_normalized]

        return None

    def _detect_study_level(
        self, message: str, history: List[MessageHistory]
    ) -> Optional[str]:
        """Detect study level from message and history."""
        full_user_context = message.lower()
        if history:
            for turn in history:
                if turn.sender == "user":
                    full_user_context += " " + turn.text.lower()

        for level, keywords in self.LEVEL_KEYWORDS.items():
            for kw in keywords:
                if kw in full_user_context:
                    logger.info(f"Study level detected: {level} (keyword: '{kw}')")
                    return level

        return None

    def _build_level_context(self, detected_level: Optional[str]) -> str:
        """Build context string based on detected study level."""
        if not detected_level:
            return (
                "\n\n[INFO SYSTÈME: NIVEAU D'ÉTUDES INCONNU]\n"
                "⚠️ Tu ne sais PAS encore quel niveau scolaire a l'utilisateur.\n"
                "1. NE PROPOSE AUCUN CURSUS SPÉCIFIQUE (ni PGE, ni MSc...).\n"
                "2. DEMANDE-LUI d'abord : 'Pour te conseiller au mieux, quel est ton niveau d'études actuel (Lycée, Bac+2, Reconversion...) ?'\n"
                "3. N'invente pas un profil à l'utilisateur.\n"
            )

        if detected_level in ["bac", "lycee"]:
            return (
                "\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = BAC/LYCÉE]\n"
                "L'utilisateur est niveau Bac/Lycée. Propose UNIQUEMENT le 'Programme Grande École' (5 ans).\n"
            )
        elif detected_level in ["bac+2", "bac+3", "bac+4", "bac+5"]:
            return (
                f"\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = {detected_level.upper()}]\n"
                "⚠️ ATTENTION : L'utilisateur a déjà un diplôme supérieur (Bac+2/3/4/5).\n"
                "1. S'il demande si le 'PGE' (Programme Grande École) est bien pour lui, CORRIGE-LE gentiment.\n"
                "   Dis-lui : 'Avec ton niveau, tu n'as pas besoin de reprendre à zéro ! Tu peux intégrer directement nos MSc Pro ou l'année Pré-MSc.'\n"
                "2. Ton objectif est de vendre les 'MSc Pro' (Spécialisation) ou l'Année Pré-MSc.\n"
            )
        elif detected_level == "reconversion":
            return (
                "\n\n[INFO SYSTÈME: NIVEAU DÉTECTÉ = RECONVERSION]\n"
                "L'utilisateur veut changer de vie. Ne propose PAS le cursus étudiant classique (PGE).\n"
                "Propose la 'Coding Academy' (Formation intensive pour adultes).\n"
            )

        return ""

    def _build_system_prompt(self, level_context: str) -> str:
        """Build the system prompt for Ollama."""
        full_campus_list_str = format_campus_list()

        return (
            "### RÔLE\n"
            "Tu es 'EpiQuoi', conseiller d'orientation Epitech. Ton but : Qualifier le profil de l'étudiant.\n\n"

            "### LANGUE (IMPORTANT)\n"
            "DETECTE LA LANGUE DE L'UTILISATEUR (Français, Anglais, Espagnol...) ET RÉPONDS DANS LA MÊME LANGUE.\n"
            "C'est primordial pour l'expérience utilisateur.\n\n"

            "### ⚠️ VÉRITÉ GÉOGRAPHIQUE - RÈGLE ABSOLUE (CRITIQUE) ⚠️\n"
            "Voici la base de données OFFICIELLE et EXCLUSIVE des campus Epitech. TU NE DOIS JAMAIS INVENTER UNE AUTRE ADRESSE.\n"
            "---------------------------------------------------------------------------------------------------------\n"
            f"{full_campus_list_str}"
            "---------------------------------------------------------------------------------------------------------\n"
            "RÈGLES IMPÉRATIVES :\n"
            "1. Si on te demande l'adresse de Paris, Lille, Bordeaux... COPIE-COLLE L'ADRESSE DE LA LISTE CI-DESSUS.\n"
            "2. Si l'utilisateur demande une ville NON listée (ex: Metz, Brest...) : TU DOIS DIRE qu'il n'y a pas de campus.\n"
            "3. N'INVENTE JAMAIS RIEN. Utilise uniquement la liste ci-dessus.\n\n"

            "### PROTOCOLE DE PROFILAGE (CRITIQUE)\n"
            "⚠️ AVANT DE DEMANDER LE NIVEAU D'ÉTUDES, VÉRIFIE SI L'UTILISATEUR L'A DÉJÀ MENTIONNÉ !\n"
            "Mots-clés : 'bac', 'stmg', 'sti2d', 'licence', 'bts', 'dut', 'master', 'reconversion', 'lycée', 'terminale'...\n"
            "SI DÉTECTÉ → Passe DIRECTEMENT aux recommandations !\n\n"

            "RECOMMANDATIONS PAR NIVEAU :\n"
            "   - Lycée/Bac (STMG, STI2D, Bac Pro...) → 'Programme Grande École' (5 ans post-bac).\n"
            "   - Bac+2/3 (BTS, DUT, Licence) → 'MSc Pro' (IA, Data, Cyber) ou 'Année Pré-MSc'.\n"
            "   - Reconversion → 'Coding Academy'.\n\n"

            "### PHASE DE CONVERSION (IMPORTANT)\n"
            "SIGNAUX D'INTÉRÊT à détecter : 'intéressant', 'cool', 'sympa', 'ça a l'air', 'je veux', 'inscription', 'oui'...\n"
            "SI SIGNAL DÉTECTÉ :\n"
            "   1. Confirme son intérêt (ex: 'Content que ça te plaise !').\n"
            "   2. Propose NATURELLEMENT de passer à l'étape suivante (contact, visite, candidature).\n"
            "   3. Donne les coordonnées du campus le plus pertinent (Localisation utilisateur OU Campus mentionné).\n"
            "      SI AUCUNE VILLE DÉTECTÉE : Donne les coordonnées génériques ou demande sa ville.\n"
            "   4. RESTE NATUREL : pas de forcing commercial.\n\n"

            "### INTERDICTIONS STRICTES\n"
            "- NE PAS METTRE DE NOTES DU GENRE '(Note: ...)' ou '(Remember: ...)' dans ta réponse. Jamais.\n"
            "- HORS-SUJET : Blague tech + STOP.\n"
            "- Cursus valides uniquement : 'Programme Grande École', 'MSc Pro', 'Coding Academy'.\n\n"

            "### TRAME\n"
            "- Direct, tutoiement, enthousiaste.\n"
            "- Ne répète pas ce que l'utilisateur a déjà dit.\n"
            "- TOUJOURS répondre dans la langue de l'utilisateur.\n"
            f"{level_context}"
        )

    def _build_messages(
        self,
        system_content: str,
        user_message: str,
        history: List[MessageHistory],
        context_extra: str,
        user_lang: str
    ) -> List[Dict[str, str]]:
        """Build messages list for Ollama."""
        messages = [{'role': 'system', 'content': system_content}]

        # Add history
        if history:
            for turn in history[-settings.max_history_messages:]:
                role = "assistant" if turn.sender == "bot" else "user"
                if not turn.isError:
                    messages.append({'role': role, 'content': turn.text})

        # Build final user message with context
        final_user_content = user_message
        if context_extra:
            final_user_content += f"\n\n(Information système : {context_extra})"

        # Add language instruction
        if user_lang != 'fr':
            final_user_content += (
                f"\n\n[CRITICAL: THE USER SPEAKS {user_lang.upper()}. "
                f"YOU MUST ANSWER IN {user_lang.upper()}. DO NOT SPEAK FRENCH.]"
            )
        else:
            final_user_content += (
                "\n\n[INSTRUCTION SYSTÈME ULTIME : "
                "RÉPONDS DANS LA MÊME LANGUE QUE LE MESSAGE DE L'UTILISATEUR]"
            )

        messages.append({'role': 'user', 'content': final_user_content})

        return messages
