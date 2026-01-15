"""Service for chat interactions with Ollama."""

import logging
import re
from typing import List, Dict, Optional, Tuple, Any

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
from app.services.degrees_service import DegreesService
from app.services.pedagogy_service import PedagogyService
from app.services.values_service import ValuesService
from app.services.geocoding_service import GeocodingService
from app.utils.campus_data import CAMPUSES, CITY_ALIASES, format_campus_list
from app.utils.language_detection import detect_language
from app.utils.tool_router import ToolRouter
from app.utils.tool_router import ToolDecision
from app.utils.epitech_faq import methodology_fr, methodology_en

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions."""

    def __init__(self):
        """Initialize chat service with dependencies."""
        self.news_service = NewsService()
        self.campus_service = CampusService()
        self.degrees_service = DegreesService()
        self.pedagogy_service = PedagogyService()
        self.values_service = ValuesService()
        self.geocoding_service = GeocodingService()

    # Keywords for intent detection
    NEWS_KEYWORDS = ["news", "actualité", "actu", "nouveauté", "événement"]

    DEGREES_KEYWORDS = [
        "diplome", "diplôme", "diplomes", "diplômes",
        "programme", "programmes", "cursus", "formation", "formations",
        "msc", "master", "master of science", "bachelor",
        "coding academy", "web@cadémie", "web@academie",
    ]
    
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
            "stl", "st2s", "bac s", "bac es", "bac l",
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
            # Detect language (debug only). We ALWAYS respond in French.
            print("🔍 [1/6] Détection de la langue (info)...")
            detected_lang = detect_language(
                request.message,
                min_words=settings.min_words_for_lang_detection
            )
            if detected_lang != "fr":
                logger.info(f"Language detected (ignored): {detected_lang}")
                print(f"   ✓ Langue détectée (ignorée): {detected_lang}")
            else:
                print("   ✓ Langue détectée: français")
            user_lang = "fr"

            # Build context from tools
            context_extra = ""
            backend_source = f"Ollama Local ({settings.ollama_model})"
            msg_lower = request.message.lower()

            def _extract_country_filter(msg_lower_val: str) -> str | None:
                """
                Return a canonical country name matching our campus data (French labels),
                based on a user query like "en Espagne".
                """
                s = msg_lower_val
                if "espagne" in s or "spain" in s:
                    return "Espagne"
                if "allemagne" in s or "germany" in s:
                    return "Allemagne"
                if "belgique" in s or "belgium" in s:
                    return "Belgique"
                if "bénin" in s or "benin" in s:
                    return "Bénin"
                if "france" in s:
                    return "France"
                return None

            def _extract_region_filter(msg_lower_val: str) -> List[str] | None:
                """
                Map French regions to campus cities we know.
                Currently used to answer queries like "région Grand Est" without listing all campuses.
                """
                s = msg_lower_val.replace("-", " ").lower()
                if ("grand est" in s) or ("grandest" in s):
                    # Grand Est: Strasbourg, Nancy, Mulhouse
                    return ["Strasbourg", "Nancy", "Mulhouse"]
                return None

            # Language preference command (should not be blocked by off-topic guard)
            if any(k in msg_lower for k in ("parle moi", "parle-moi", "reponds", "réponds")) and any(
                k in msg_lower for k in ("en francais", "en français", "francais", "français")
            ):
                return {
                    "response": "Compris. Je te réponds en **français** à partir de maintenant. Pose-moi ta question sur Epitech.",
                    "backend_source": "Preference (language=fr)",
                }

            # We intentionally do NOT support switching away from French.
            if any(k in msg_lower for k in ("in english", "english", "en anglais", "anglais", "speak english", "reply in english", "answer in english")):
                return {
                    "response": "Je réponds uniquement en **français**. Pose-moi ta question sur Epitech.",
                    "backend_source": "Preference (language=fr-only)",
                }

            # "Devise / valeurs" Epitech: always use official source (no hallucination).
            if ("epitech" in msg_lower) and any(k in msg_lower for k in ("devise", "valeur", "valeurs")):
                wants_source = any(k in msg_lower for k in ("source", "sources", "lien", "liens", "url", "officiel"))
                values_payload = await self.values_service.get_values_info()
                if values_payload and isinstance(values_payload, dict):
                    data = values_payload.get("data", {}) if isinstance(values_payload.get("data"), dict) else {}
                    sentence = data.get("values_sentence")
                    url = data.get("url")
                    if sentence:
                        resp = sentence
                        if wants_source and url:
                            resp += f"\n\nSource : {url}"
                        return {"response": resp, "backend_source": "MCP Tool (values)"}
                # Fallback if tool fails
                resp = "Chez Epitech, nous croyons en nos valeurs, que sont l'excellence, le courage et la solidarité."
                return {"response": resp, "backend_source": "Fallback (values)"}

            # If user mixes Epitech + unrelated requests (recipes, games...), answer ONLY the Epitech part.
            off_topic_keywords = [
                "recette", "omelette", "omelette", "omelet", "cuisine", "minecraft", "hache",
                "bonheur", "soeur", "sœur",
            ]
            has_offtopic = any(k in msg_lower for k in off_topic_keywords)
            has_epitech = ("epitech" in msg_lower) or any(
                k in msg_lower for k in ["campus", "formation", "formations", "programme", "dipl", "msc", "bachelor", "mba", "pédagogie", "pedagogie", "méthodologie", "methodologie"]
            )
            if has_epitech and has_offtopic:
                # If campus list is requested, return a safe deterministic answer from the campus tool.
                if "campus" in msg_lower or "campuses" in msg_lower:
                    campus_data = await self.campus_service.get_campus_info()
                    optimized = self._optimize_campus_data(campus_data)
                    country_filter = _extract_country_filter(msg_lower)
                    if country_filter:
                        optimized = [c for c in optimized if (c.get("pays") or "").lower() == country_filter.lower()]
                    region_filter = _extract_region_filter(msg_lower)
                    if region_filter:
                        allowed = {c.lower() for c in region_filter}
                        optimized = [c for c in optimized if (c.get("ville") or "").lower() in allowed]
                    campus_text = self._format_campus_to_text(optimized)
                    return {
                        "response": (
                            f"Voici les campus Epitech ({len(optimized)}) :\n{campus_text}\n\n"
                            "Je ne peux pas répondre à la recette/au sujet non lié à Epitech ici. Pose-moi une question Epitech (campus, formations, admissions, pédagogie)."
                        ),
                        "backend_source": "Scraper Campus (filtered)",
                    }
                # Otherwise: refuse the off-topic part but keep conversation on Epitech.
                return {
                    "response": (
                        "Je réponds uniquement à Epitech (campus, formations, admissions, pédagogie). "
                        "Repose ta question Epitech seule et je te réponds."
                    ),
                    "backend_source": "Off-topic (mixed)",
                }

            # Conversation-aware context: user may omit "Epitech" in a follow-up.
            def _has_epitech_context() -> bool:
                if "epitech" in msg_lower:
                    return True
                # Look at a few recent turns for "epitech" (user or assistant)
                for turn in reversed(request.history[-6:]):
                    if "epitech" in (turn.text or "").lower():
                        return True
                return False

            def _degrees_followup_context() -> bool:
                """
                Detect a follow-up like:
                  user: "quelles formations ?"
                  bot: "Tu parles des formations d'Epitech ? ... niveau + ville"
                  user: "bac+3"
                In that case, we SHOULD call the degrees tool even if the current message has no keywords.
                """
                # Current message is likely just a level/short confirmation
                short = len(msg_lower.strip()) <= 20
                looks_like_level = any(
                    k in msg_lower
                    for k in (
                        "bac+",
                        "bac +",
                        "bts",
                        "dut",
                        "licence",
                        "master",
                        "reconversion",
                        "lycée",
                        "lycee",
                    )
                )
                if not (short and looks_like_level):
                    return False

                # Recent assistant prompt asking about Epitech formations/programmes/specialisations
                for turn in reversed(request.history[-4:]):
                    if turn.sender == "bot":
                        t = (turn.text or "").lower()
                        if (
                            ("formations" in t or "programme" in t or "dipl" in t or "spécialisation" in t or "specialisation" in t)
                            and ("epitech" in t)
                            and (("bachelor" in t) or ("msc" in t) or ("master of science" in t) or ("pré-msc" in t) or ("pre-msc" in t))
                        ):
                            return True
                return False

            epitech_context = _has_epitech_context()
            degrees_followup = _degrees_followup_context()

            # Off-topic guard must be based on the CURRENT message, even if the conversation previously mentioned Epitech.
            # Otherwise the model will answer anything (Minecraft, etc.) just because earlier turns were about Epitech.
            epitech_related_hints_current = (
                ("epitech" in msg_lower)
                or ("campus" in msg_lower)
                or ("formation" in msg_lower)
                or ("formations" in msg_lower)
                or ("programme" in msg_lower)
                or ("programmes" in msg_lower)
                or ("dipl" in msg_lower)
                or ("specialisation" in msg_lower)
                or ("spécialisation" in msg_lower)
                or ("specialisations" in msg_lower)
                or ("spécialisations" in msg_lower)
                or ("msc" in msg_lower)
                or ("bachelor" in msg_lower)
                or ("mba" in msg_lower)
                or ("coding academy" in msg_lower)
                or ("web@cad" in msg_lower)
                or ("admission" in msg_lower)
                or ("inscription" in msg_lower)
                or ("pédagogie" in msg_lower)
                or ("pedagogie" in msg_lower)
                or ("méthodologie" in msg_lower)
                or ("methodologie" in msg_lower)
            )


            # Allow tiny follow-ups that rely on previous context (level confirmations, yes/no, city).
            msg_stripped = msg_lower.strip()
            
            # Phrases de suivi naturelles qui indiquent une continuation
            followup_phrases = {
                "oui", "non", "ok", "daccord", "d'accord", "merci", "yes", "no",
                "plus d'info", "plus d'infos", "plus d'information", "plus d'informations",
                "je veux bien", "je veux savoir", "dis-moi", "dis moi", "explique",
                "continue", "va-y", "vas-y", "et ensuite", "quoi d'autre",
                "comment", "pourquoi", "c'est quoi", "c'est-à-dire", "ça m'intéresse",
                "interessant", "intéressant", "super", "genial", "génial", "cool",
                "je suis intéressé", "je suis interessé", "ça a l'air bien",
                "en savoir plus", "j'aimerais savoir", "peux-tu m'expliquer",
            }
            
            # Vérifie si une des phrases de suivi est présente dans le message
            has_followup_phrase = any(phrase in msg_stripped for phrase in followup_phrases)
            
            # Vérifie si le dernier message du bot parlait d'Epitech (contexte valide pour un suivi)
            def _last_bot_was_epitech() -> bool:
                for turn in reversed(request.history[-4:]):
                    if turn.sender == "bot" and not turn.isError:
                        bot_text = (turn.text or "").lower()
                        # Le bot a parlé de campus, formations, ou Epitech
                        if any(kw in bot_text for kw in ["epitech", "campus", "formation", "msc", "bachelor", "pge", "programme"]):
                            return True
                        break  # On ne regarde que le dernier message bot
                return False
            
            last_bot_epitech = _last_bot_was_epitech()
            
            # Patterns qui indiquent une référence au contexte précédent
            context_reference_patterns = [
                r"je t'ai (dit|dis)", r"je t'avais (dit|dis)", r"comme je (t'ai |te l'ai |l'ai )",
                r"tu m'as (dit|demandé)", r"ma question", r"ma demande",
                r"je viens de", r"j'habite", r"je suis de", r"et le campus", r"et du coup",
                r"quel campus", r"lequel", r"où ça", r"c'est où",
            ]
            has_context_reference = any(re.search(p, msg_stripped) for p in context_reference_patterns)
            
            is_short_followup = (
                len(msg_stripped) <= 80  # Augmenté pour permettre des phrases de contexte
                and (
                    degrees_followup
                    or has_followup_phrase
                    or has_context_reference  # Référence explicite au contexte
                    or (last_bot_epitech and len(msg_stripped) <= 50)  # Message court après réponse Epitech
                    or re.search(r"\bbac\s*\+\s*\d\b", msg_stripped) is not None
                    or any(city.lower() == msg_stripped for city in CAMPUSES.keys())
                )
            )

            if not epitech_related_hints_current and not is_short_followup:
                if user_lang != "fr":
                    return {
                        "response": "I’m EpiQuoi — I only handle Epitech questions (campuses, programs, admissions). What would you like to know about Epitech?",
                        "backend_source": "Off-topic",
                    }
                return {
                    "response": "Je suis **EpiQuoi** : je réponds uniquement aux questions liées à **Epitech** (campus, formations, admissions). Tu veux savoir quoi sur Epitech ?",
                    "backend_source": "Off-topic",
                }

            # If it's a methodology/pedagogy question, prefer the official page via MCP tool.
            # If the tool fails, fallback to the trusted FAQ snippet.
            if epitech_context and any(k in msg_lower for k in ("méthodologie", "methodologie", "pédagogie", "pedagogie", "pédago", "pedago")):
                tool_decisions = ToolRouter.route(request.message, epitech_context=epitech_context)
                if tool_decisions.get("pedagogy") and tool_decisions["pedagogy"].call:
                    pedagogy_data = await self.pedagogy_service.get_pedagogy_info()
                    if pedagogy_data and isinstance(pedagogy_data, dict):
                        p = pedagogy_data.get("data", {}) if isinstance(pedagogy_data.get("data"), dict) else {}
                        pillars = p.get("pillars") or []
                        pillars_txt = ", ".join(pillars) if isinstance(pillars, list) and pillars else None
                        url = p.get("url")
                        if user_lang != "fr":
                            return {
                                "response": (
                                    "Epitech’s pedagogy is mainly **project-based learning** (active learning).\n"
                                    f"- **Core pillars**: {pillars_txt or 'practice, collaboration, teamwork, communication'}\n"
                                    "- **Goal**: learn by building, reasoning, and solving problems.\n\n"
                                    f"Official page: {url}" if url else ""
                                ).strip(),
                                "backend_source": "MCP Tool (pedagogy)",
                            }
                        return {
                            "response": (
                                "La pédagogie Epitech est surtout une **pédagogie par projets** (pédagogie active).\n"
                                f"- **Piliers** : {pillars_txt or 'la pratique, la collaboration, l’esprit d’équipe, la communication'}\n"
                                "- **Objectif** : apprendre en construisant, raisonner, acquérir une méthode de résolution de problèmes.\n\n"
                                f"Source officielle : {url}" if url else ""
                            ).strip(),
                            "backend_source": "MCP Tool (pédagogie)",
                        }

                # Fallback
                if user_lang != "fr":
                    return {"response": methodology_en(), "backend_source": "FAQ (methodology)"}
                return {"response": methodology_fr(), "backend_source": "FAQ (méthodologie)"}

            # (off-topic guard handled earlier using current message content)

            # If user asks about programs/specializations without saying "Epitech",
            # we still prefer scraping (to avoid hallucinations) and we ask 1 short clarification in the final answer.
            needs_track_clarification = False
            if (
                ("formation" in msg_lower)
                or ("formations" in msg_lower)
                or ("programme" in msg_lower)
                or ("dipl" in msg_lower)
                or ("specialisation" in msg_lower)
                or ("spécialisation" in msg_lower)
                or ("specialisations" in msg_lower)
                or ("spécialisations" in msg_lower)
            ) and not epitech_context:
                needs_track_clarification = True

            tool_decisions = ToolRouter.route(request.message, epitech_context=epitech_context)
            if degrees_followup and not tool_decisions["degrees"].call:
                tool_decisions["degrees"] = ToolDecision(
                    call=True,
                    score=tool_decisions["degrees"].score,
                    reasons=tool_decisions["degrees"].reasons + ["forced follow-up (level answer after formations question)"],
                )

            # If it's clearly Epitech-related but router is unsure, do a light speculative scrape in parallel
            # (campus + degrees) to avoid hallucinations.
            if epitech_context and not any(d.call for d in tool_decisions.values()):
                if any(k in msg_lower for k in ("campus", "ville", "adresse", "formation", "formations", "programme", "dipl")):
                    tool_decisions["campus"] = ToolDecision(
                        call=True,
                        score=tool_decisions["campus"].score,
                        reasons=tool_decisions["campus"].reasons + ["speculative scrape (ambiguous epitech question)"],
                    )
                    tool_decisions["degrees"] = ToolDecision(
                        call=True,
                        score=tool_decisions["degrees"].score,
                        reasons=tool_decisions["degrees"].reasons + ["speculative scrape (ambiguous epitech question)"],
                    )
            print(
                "🧰 [ROUTER] Décisions tools: "
                f"news(call={tool_decisions['news'].call}, score={tool_decisions['news'].score:.1f}) | "
                f"campus(call={tool_decisions['campus'].call}, score={tool_decisions['campus'].score:.1f}) | "
                f"degrees(call={tool_decisions['degrees'].call}, score={tool_decisions['degrees'].score:.1f}) | "
                f"pedagogy(call={tool_decisions.get('pedagogy').call if tool_decisions.get('pedagogy') else False}, "
                f"score={tool_decisions.get('pedagogy').score if tool_decisions.get('pedagogy') else 0.0:.1f})"
            )

            # Run selected tools in parallel (faster when multiple tools are needed).
            import asyncio

            tool_tasks: Dict[str, asyncio.Task] = {}
            if tool_decisions["news"].call:
                tool_tasks["news"] = asyncio.create_task(self.news_service.get_epitech_news())
            if tool_decisions["campus"].call:
                tool_tasks["campus"] = asyncio.create_task(self.campus_service.get_campus_info())
            if tool_decisions["degrees"].call:
                tool_tasks["degrees"] = asyncio.create_task(self.degrees_service.get_degrees_info())
            if tool_decisions.get("pedagogy") and tool_decisions["pedagogy"].call:
                tool_tasks["pedagogy"] = asyncio.create_task(self.pedagogy_service.get_pedagogy_info())

            # Tool 1: News Scraper
            print("🔍 [2/6] Vérification si scraper NEWS nécessaire...")
            if tool_decisions["news"].call:
                print("   ⚡ SCRAPER NEWS ACTIVÉ - Démarrage...")
                if tool_decisions["news"].reasons:
                    print(f"   ↳ raisons: {', '.join(tool_decisions['news'].reasons[:6])}")
                logger.info("Tool Activation: Scraper Epitech News")
                news_info = await tool_tasks["news"]
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
            if tool_decisions["campus"].call:
                print("   ⚡ SCRAPER CAMPUS ACTIVÉ - Démarrage...")
                if tool_decisions["campus"].reasons:
                    print(f"   ↳ raisons: {', '.join(tool_decisions['campus'].reasons[:6])}")
                logger.info("Tool Activation: Scraper Campus")
                campus_data = await tool_tasks["campus"]
                
                if campus_data:
                    # MCP returns {"data": [...], "meta": {...}}
                    if isinstance(campus_data, dict) and isinstance(campus_data.get("data"), list):
                        print(
                            "   ✓ Scraping campus terminé : "
                            f"{len(campus_data.get('data', []))} campus détectés (via MCP.data)"
                        )
                    elif isinstance(campus_data, list):
                        print(f"   ✓ Scraping campus terminé : {len(campus_data)} campus détectés (list brute)")
                    else:
                        print(
                            f"   ⚠️ Format de données inattendu : {type(campus_data)} "
                            "(attendu: dict{data} ou list)"
                        )
                    
                    # Optimize data to prevent context overflow (OOM)
                    optimized_data = self._optimize_campus_data(campus_data)

                    # Apply country filter if the user asked "campus en <pays>"
                    country_filter = _extract_country_filter(msg_lower)
                    if country_filter:
                        before = len(optimized_data)
                        optimized_data = [
                            c for c in optimized_data if (c.get("pays") or "").lower() == country_filter.lower()
                        ]
                        print(f"   ✓ Filtre pays '{country_filter}' : {before} -> {len(optimized_data)} campus")

                    # Apply region filter if the user asked "campus en région <...>"
                    region_filter = _extract_region_filter(msg_lower)
                    if region_filter:
                        before = len(optimized_data)
                        allowed = {c.lower() for c in region_filter}
                        optimized_data = [c for c in optimized_data if (c.get("ville") or "").lower() in allowed]
                        print(f"   ✓ Filtre région '{' / '.join(region_filter)}' : {before} -> {len(optimized_data)} campus")

                    print(f"   ✓ Données optimisées : {len(optimized_data)} campus conservés après filtrage")
                    
                    # Convert to text to save tokens (JSON is too heavy)
                    campus_text = self._format_campus_to_text(optimized_data)
                    print(f"   ✓ Texte généré pour le prompt (DEBUG) :\n{campus_text}")
                    
                    total_campus = len(optimized_data)
                    context_extra += (
                        f"\n\n[SYSTÈME: DONNÉES CAMPUS LIVE - {total_campus} CAMPUS]\n"
                        f"⚠️ IMPORTANT : Il y a EXACTEMENT {total_campus} campus dans cette liste. "
                        f"Si l'utilisateur demande les campus d'un pays ou d'une région (ex: Espagne, Grand Est), réponds UNIQUEMENT avec ces campus filtrés.\n"
                        f"Même si les formations sont identiques (ex: Madrid/Barcelone), CITE CHAQUE VILLE SÉPARÉMENT.\n\n"
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

            # Tool 1.7: Degrees / Programmes Scraper (Live)
            print("🔍 [2.7/6] Vérification demande scraping diplômes/programmes...")
            if tool_decisions["degrees"].call:
                print("   ⚡ SCRAPER DEGREES ACTIVÉ - Démarrage...")
                if tool_decisions["degrees"].reasons:
                    print(f"   ↳ raisons: {', '.join(tool_decisions['degrees'].reasons[:6])}")
                logger.info("Tool Activation: Scraper Degrees")
                degrees_data = await tool_tasks["degrees"]

                if degrees_data and isinstance(degrees_data, dict):
                    items = degrees_data.get("data", [])
                    print(f"   ✓ Scraping degrees terminé : {len(items)} programmes")

                    # Build a compact, source-first block (LLM must cite URLs).
                    sources: list[str] = []
                    blocks: list[str] = []
                    for prog in items:
                        if not isinstance(prog, dict):
                            continue
                        nom = prog.get("nom")
                        niveau = prog.get("niveau")
                        cat = prog.get("categorie")
                        pages = prog.get("pages", []) if isinstance(prog.get("pages"), list) else []

                        header_parts = [p for p in [nom, cat, niveau] if p]
                        header = " - ".join(header_parts) if header_parts else "Programme"

                        # Keep only a few page snippets in the prompt (avoid token explosion),
                        # but keep ALL URLs in Sources.
                        page_lines: list[str] = []
                        for p in pages:
                            if not isinstance(p, dict):
                                continue
                            url = p.get("url")
                            if isinstance(url, str):
                                sources.append(url)
                            title = p.get("h1") or p.get("title")
                            desc = p.get("description")
                            snippet = p.get("snippet")
                            duration_hints = p.get("duration_hints") if isinstance(p.get("duration_hints"), list) else []
                            line = f"- {title}" if title else "- Page"
                            if snippet and isinstance(snippet, str):
                                line += f": {snippet[:220]}{'…' if len(snippet) > 220 else ''}"
                            if duration_hints:
                                # Show at most 2 duration hints to keep it compact.
                                dh = ", ".join([str(x) for x in duration_hints[:2]])
                                line += f" (Durée repérée: {dh})"
                            if url:
                                line += f" (Source: {url})"
                            # Show max 2 lines per programme to keep prompt small
                            page_lines.append(line)
                            if len(page_lines) >= 2:
                                break

                        blocks.append(header + "\n" + "\n".join(page_lines))

                    # Deduplicate sources while preserving order
                    seen = set()
                    uniq_sources: list[str] = []
                    for u in sources:
                        if u in seen:
                            continue
                        seen.add(u)
                        uniq_sources.append(u)

                    degrees_text = "\n\n".join(blocks) if blocks else "Aucune donnée exploitable."
                    context_extra += (
                        "\n\n[SYSTÈME: DONNÉES DIPLÔMES/PROGRAMMES LIVE]\n"
                        "Voici les informations OFFICIELLES scrapées (avec sources) :\n"
                        f"{degrees_text}\n\n"
                        "SOURCES (à afficher dans la réponse) :\n"
                        + "\n".join(f"- {u}" for u in uniq_sources[:25])
                        + ("\n- ... (autres sources disponibles)" if len(uniq_sources) > 25 else "")
                        + "\n\n"
                        "RÈGLES STRICTES :\n"
                        "- Commence ta réponse par **1 phrase de reformulation** (ex: \"Si je reformule, tu veux la liste des spécialisations Epitech...\").\n"
                        "- N'INVENTE PAS de spécialités/secteurs (ex: santé, énergie, biotech...) si ce n'est pas dans la liste ci-dessus.\n"
                        "- N'INVENTE PAS de durées (1 an / 2 ans / etc.) : ne donne une durée que si elle apparaît dans les lignes \"Durée repérée\" ci-dessus, et cite la page correspondante.\n"
                        "- Si l'utilisateur demande le **MBA**, et que des pages MBA sont dans les SOURCES, tu DOIS confirmer que le MBA existe et répondre UNIQUEMENT avec ces pages (ne le nie jamais).\n"
                        "- Si l'utilisateur demande le détail des spécialisations, dis que tu peux expliquer les grandes familles (PGE/MSc/Coding Academy) mais que tu n'as pas le catalogue complet.\n"
                        "- Quand tu donnes un détail (programme/specialisation), ajoute la/les URL(s) correspondantes en 'Sources:' à la fin.\n"
                        "Utilise ces données comme source prioritaire si l'utilisateur demande les diplômes, programmes ou cursus."
                    )
                    if needs_track_clarification:
                        context_extra += (
                            "\n\n[INSTRUCTION]\n"
                            "L'utilisateur n'a pas précisé s'il parle du Bachelor ou des MSc/MBA. "
                            "Après avoir donné une liste courte et fiable (avec sources), pose UNE question: "
                            "\"Tu vises le Bachelor ou les MSc/MBA, et tu es à quel niveau (Bac+2/Bac+3/reconversion)?\""
                        )
                    backend_source += " + Scraper Degrees"
                else:
                    print("   ⚠️ Échec du scraping degrees")
            else:
                print("   → Pas de scraping diplômes/programmes demandé")

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
            # If the campus tool doesn't provide per-campus program lists, don't show a misleading placeholder.
            if c.get("formations"):
                forms = ", ".join(c["formations"][:3])
                if len(c["formations"]) > 3:
                    forms += f" (+{len(c['formations']) - 3} autres)"
                lines.append(f"{idx}. {ville} ({pays}) : {forms}")
            else:
                lines.append(f"{idx}. {ville} ({pays})")
        return "\n".join(lines)

    def _optimize_campus_data(self, data: Any) -> List[Dict]:
        """Optimize and filter campus data to reduce token usage."""
        optimized = []
        # MCP Server returns {"data": [...], "meta": {...}}
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            data = data.get("data")
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
                "url": campus.get("url"),
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

    # NOTE: Tool routing is handled by app.utils.tool_router.ToolRouter.

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

        # Prefer explicit "bac+N" patterns before keyword scanning (avoids matching "bac " in "bac +2").
        m = re.search(r"\bbac\s*\+\s*(\d)\b", full_user_context)
        if m:
            n = m.group(1)
            if n in {"2", "3", "4", "5"}:
                return f"bac+{n}"
            if n == "0":
                return "bac"

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

            "### ⚠️ CONVERSATION EN COURS (CRITIQUE) ⚠️\n"
            "Tu es en MILIEU de conversation. L'historique des messages précédents t'est fourni.\n"
            "RÈGLES ABSOLUES :\n"
            "1. Ne dis PAS 'Bonjour' si tu as déjà parlé à cet utilisateur (vérifie l'historique).\n"
            "2. RAPPELLE-TOI des informations données : ville/localisation, niveau d'études, préférences.\n"
            "3. Si l'utilisateur te rappelle quelque chose ('je t'ai dit...'), excuse-toi et utilise cette info.\n"
            "4. Quand on te demande 'quel campus', utilise la LOCALISATION mentionnée dans l'historique.\n\n"

            "### FAITS (ANTI-HALLUCINATION)\n"
            "- Epitech est une **école** (pas une université). Ne dis JAMAIS \"Université Epitech\".\n\n"

            "### LANGUE (IMPORTANT)\n"
            "Tu réponds UNIQUEMENT en **français**.\n\n"

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

        # Always answer in French
        final_user_content += (
            "\n\n[INSTRUCTION SYSTÈME ULTIME : "
            "RÉPONDS UNIQUEMENT EN FRANÇAIS]"
        )

        messages.append({'role': 'user', 'content': final_user_content})

        return messages
