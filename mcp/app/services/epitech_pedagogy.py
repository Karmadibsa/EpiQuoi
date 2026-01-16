from __future__ import annotations

import re
import time
from html import unescape
from typing import Any, Dict, Tuple

import httpx


PEDAGOGY_URL = "https://www.epitech.eu/ecole-informatique-apres-bac/pedagogie/"


def _strip_tags(html: str) -> str:
    # Remove script/style blocks first
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    # Strip all tags
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _extract_after(label: str, text: str, max_len: int = 280) -> str | None:
    """
    Extract a short snippet after a label (e.g., "Ses piliers :").
    We keep it short to avoid injecting huge pages into the LLM context.
    """
    idx = text.lower().find(label.lower())
    if idx == -1:
        return None
    frag = text[idx : idx + max_len]
    # Try to cut at sentence boundary
    m = re.search(r"([.!?])\s", frag)
    if m:
        frag = frag[: m.end(1)]
    return frag.strip()


def _extract_pillars(text: str) -> list[str]:
    # The official page contains: "Ses piliers : la pratique, la collaboration, ..."
    snippet = _extract_after("Ses piliers", text, max_len=240) or ""
    # Keep only after ":" if present
    if ":" in snippet:
        snippet = snippet.split(":", 1)[1]
    # Split by commas
    parts = [p.strip(" .;:") for p in snippet.split(",")]
    parts = [p for p in parts if p and len(p) <= 40]
    # Deduplicate, keep order
    out: list[str] = []
    seen = set()
    for p in parts:
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out[:8]


async def scrape_pedagogy(timeout_sec: int, user_agent: str) -> Tuple[Dict[str, Any], int]:
    """
    Returns (pedagogy_data, duration_ms)
    """
    headers = {"User-Agent": user_agent}
    start = time.time()
    async with httpx.AsyncClient(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        r = await client.get(PEDAGOGY_URL)
        r.raise_for_status()
        html = r.text or ""
    duration_ms = int((time.time() - start) * 1000)

    text = _strip_tags(html)

    data: Dict[str, Any] = {
        "url": PEDAGOGY_URL,
        "source": "epitech.eu",
        "headline": None,
        "summary": None,
        "pillars": _extract_pillars(text),
        "objective": _extract_after("L’objectif", text, max_len=320),
        "key_quote": _extract_after("Née à Epitech", text, max_len=320),
    }

    # Headline / summary heuristics based on known wording on the page
    h = _extract_after("Avec la pédagogie par projet", text, max_len=220)
    if h:
        data["headline"] = h
    s = _extract_after("Comment fonctionne la pédagogie Epitech", text, max_len=420)
    if s:
        data["summary"] = s

    return data, duration_ms

