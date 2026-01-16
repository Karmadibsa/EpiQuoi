"""Tool routing (intent detection) for MCP tools.

Goal: decide *when* to call external tools (scrapers, etc.) from messy user text.
We keep this deterministic, fast, and debuggable (scores + reasons).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ToolDecision:
    call: bool
    score: float
    reasons: List[str]


class ToolRouter:
    """
    Simple scoring router with guardrails.

    - Uses keyword + pattern scoring (robust to typos/short prompts)
    - Requires "epitech" mention for non-explicit tool calls (reduces false positives)
    - Allows explicit override: "scrape/scraper" => call tools if relevant keywords exist
    """

    # Common signals
    EPITECH_HINTS = ("epitech", "epi tech", "epi-tech")
    EXPLICIT_TOOL_HINTS = ("scrape", "scraper", "scraping", "crawl", "crawler")

    # Tool-specific keywords
    CAMPUS_HINTS = (
        "campus",
        "cite",
        "citer",
        "ville",
        "pays",
        "international",
        "où",
        "ou",
        "adresse",
        "implantation",
        "liste",
        "lister",
        "quels",
        "quelles",
        "combien",
        "il y a",
        "site",
        "contact",
        # Countries / common campus queries
        "espagne",
        "spain",
        # Cities (common international)
        "madrid",
        "barcelone",
    )
    DEGREES_HINTS = (
        "diplome",
        "diplôme",
        "diplomes",
        "diplômes",
        "specialisation",
        "spécialisation",
        "specialisations",
        "spécialisations",
        "programme",
        "programmes",
        "cursus",
        "formation",
        "formations",
        "msc",
        "mba",
        "master",
        "master of science",
        "bachelor",
        "coding academy",
        "web@cadémie",
        "web@academie",
        "grande ecole",
        "grande école",
    )
    
    # Domaines d'études - quand l'utilisateur mentionne un domaine, on doit scraper les formations
    DOMAIN_HINTS = (
        # Domaines techniques
        "cyber", "cybersécurité", "sécurité",
        "data", "données", "big data", "analytics",
        "intelligence artificielle", "machine learning", "deep learning",
        "cloud", "web3", "blockchain",
        "iot", "objets connectés", "robotique",
        "réalité virtuelle", "vr", "immersif",
        # Domaines métiers (MBA)
        "santé", "health", "medtech",
        "fintech", "finance",
        "marketing", "influence",
        "management", "business", "entrepreneuriat",
        "luxe", "retail",
        "ressources humaines",
        # Questions d'orientation
        "travailler dans", "bosser dans", "faire du", "me spécialiser",
        "quel domaine", "quels débouchés", "après le diplôme",
    )
    
    NEWS_HINTS = ("news", "actualité", "actu", "nouveauté", "événement")
    PEDAGOGY_HINTS = ("méthodologie", "methodologie", "pédagogie", "pedagogie", "pédago", "pedago")

    # Thresholds (tuned for "chatty" users)
    THRESH_CAMPUS = 2.0
    THRESH_DEGREES = 1.5  # Abaissé pour mieux détecter les questions de domaines
    THRESH_NEWS = 2.5
    THRESH_PEDAGOGY = 1.5

    @classmethod
    def route(cls, user_text: str, *, epitech_context: bool = False) -> Dict[str, ToolDecision]:
        msg = (user_text or "").strip()
        lower = msg.lower()

        def has_any(needles: Tuple[str, ...]) -> bool:
            return any(n in lower for n in needles)

        epitech_mentioned = epitech_context or has_any(cls.EPITECH_HINTS)
        explicit_tool = has_any(cls.EXPLICIT_TOOL_HINTS)

        decisions: Dict[str, ToolDecision] = {}

        # --- CAMPUS ---
        campus_score = 0.0
        campus_reasons: List[str] = []
        for k in cls.CAMPUS_HINTS:
            if k in lower:
                campus_score += 1.0
                campus_reasons.append(f"+1 '{k}'")
        if epitech_mentioned:
            campus_score += 1.0
            campus_reasons.append("+1 epitech mention")
        if explicit_tool:
            campus_score += 0.5
            campus_reasons.append("+0.5 explicit tool hint")

        # Campus is safe/cheap and frequently asked without "Epitech" in the message.
        # So we allow campus scraping based on score alone (still requires campus-like wording).
        campus_call = (explicit_tool and campus_score >= 1.5) or (
            campus_score >= cls.THRESH_CAMPUS and "campus" in lower
        )
        decisions["campus"] = ToolDecision(call=campus_call, score=campus_score, reasons=campus_reasons)

        # --- DEGREES ---
        degrees_score = 0.0
        degrees_reasons: List[str] = []
        for k in cls.DEGREES_HINTS:
            if k in lower:
                degrees_score += 1.0
                degrees_reasons.append(f"+1 '{k}'")

        # Special case: "spécialisations ?" is a very common query in this app.
        # Give it extra weight so it can trigger scraping even without "Epitech" in the message.
        if any(s in lower for s in ("specialisation", "spécialisation", "specialisations", "spécialisations")):
            degrees_score += 1.0
            degrees_reasons.append("+1 specialization question boost")
        
        # Domaines d'études mentionnés - l'utilisateur parle d'orientation/carrière
        domain_mentioned = False
        for domain in cls.DOMAIN_HINTS:
            if domain in lower:
                degrees_score += 1.5  # Fort boost pour les domaines
                degrees_reasons.append(f"+1.5 domain '{domain}'")
                domain_mentioned = True
                break  # Un seul bonus de domaine

        if epitech_mentioned:
            degrees_score += 1.0
            degrees_reasons.append("+1 epitech mention")
        if explicit_tool:
            degrees_score += 0.5
            degrees_reasons.append("+0.5 explicit tool hint")

        # Allow degrees scraping without explicit "Epitech" if the question is clearly about programs/specializations.
        degrees_topic = any(
            t in lower
            for t in (
                "formation",
                "formations",
                "programme",
                "programmes",
                "dipl",
                "specialisation",
                "spécialisation",
                "specialisations",
                "spécialisations",
                "msc",
                "bachelor",
                "mba",
                "master",
            )
        )
        
        # Déclencher le scraping si:
        # 1. Question explicite sur les formations ET score suffisant
        # 2. Domaine mentionné (santé, cyber, etc.) - toujours scraper pour avoir les vraies formations
        degrees_call = (
            (explicit_tool and degrees_score >= 1.5) 
            or (degrees_topic and degrees_score >= cls.THRESH_DEGREES)
            or domain_mentioned  # NOUVEAU: toujours scraper si domaine mentionné
        )
        decisions["degrees"] = ToolDecision(call=degrees_call, score=degrees_score, reasons=degrees_reasons)

        # --- NEWS ---
        news_score = 0.0
        news_reasons: List[str] = []
        for k in cls.NEWS_HINTS:
            if k in lower:
                news_score += 1.0
                news_reasons.append(f"+1 '{k}'")
        if epitech_mentioned:
            news_score += 1.0
            news_reasons.append("+1 epitech mention")
        if explicit_tool:
            news_score += 0.5
            news_reasons.append("+0.5 explicit tool hint")

        news_call = (explicit_tool and news_score >= 2.0) or (
            epitech_mentioned and news_score >= cls.THRESH_NEWS
        )
        decisions["news"] = ToolDecision(call=news_call, score=news_score, reasons=news_reasons)

        # --- PEDAGOGY ---
        pedagogy_score = 0.0
        pedagogy_reasons: List[str] = []
        for k in cls.PEDAGOGY_HINTS:
            if k in lower:
                pedagogy_score += 1.0
                pedagogy_reasons.append(f"+1 '{k}'")
        if epitech_mentioned:
            pedagogy_score += 1.0
            pedagogy_reasons.append("+1 epitech mention")
        if explicit_tool:
            pedagogy_score += 0.5
            pedagogy_reasons.append("+0.5 explicit tool hint")

        pedagogy_call = epitech_mentioned and pedagogy_score >= cls.THRESH_PEDAGOGY
        decisions["pedagogy"] = ToolDecision(call=pedagogy_call, score=pedagogy_score, reasons=pedagogy_reasons)

        return decisions

