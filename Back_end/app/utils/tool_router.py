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
        "ville",
        "où",
        "ou",
        "adresse",
        "implantation",
        "liste",
        "lister",
        "combien",
        "il y a",
        "site",
        "contact",
    )
    DEGREES_HINTS = (
        "diplome",
        "diplôme",
        "diplomes",
        "diplômes",
        "programme",
        "programmes",
        "cursus",
        "formation",
        "formations",
        "msc",
        "master",
        "master of science",
        "bachelor",
        "coding academy",
        "web@cadémie",
        "web@academie",
        "grande ecole",
        "grande école",
    )
    NEWS_HINTS = ("news", "actualité", "actu", "nouveauté", "événement")

    # Thresholds (tuned for "chatty" users)
    THRESH_CAMPUS = 2.0
    THRESH_DEGREES = 2.0
    THRESH_NEWS = 2.5

    @classmethod
    def route(cls, user_text: str) -> Dict[str, ToolDecision]:
        msg = (user_text or "").strip()
        lower = msg.lower()

        def has_any(needles: Tuple[str, ...]) -> bool:
            return any(n in lower for n in needles)

        epitech_mentioned = has_any(cls.EPITECH_HINTS)
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

        campus_call = (explicit_tool and campus_score >= 1.5) or (
            epitech_mentioned and campus_score >= cls.THRESH_CAMPUS
        )
        decisions["campus"] = ToolDecision(call=campus_call, score=campus_score, reasons=campus_reasons)

        # --- DEGREES ---
        degrees_score = 0.0
        degrees_reasons: List[str] = []
        for k in cls.DEGREES_HINTS:
            if k in lower:
                degrees_score += 1.0
                degrees_reasons.append(f"+1 '{k}'")
        if epitech_mentioned:
            degrees_score += 1.0
            degrees_reasons.append("+1 epitech mention")
        if explicit_tool:
            degrees_score += 0.5
            degrees_reasons.append("+0.5 explicit tool hint")

        degrees_call = (explicit_tool and degrees_score >= 1.5) or (
            epitech_mentioned and degrees_score >= cls.THRESH_DEGREES
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

        return decisions

