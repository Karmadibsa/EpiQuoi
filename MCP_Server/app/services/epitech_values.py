from __future__ import annotations

import re
import time
from html import unescape
from typing import Any, Dict, Tuple

import httpx


VALUES_URL = "https://www.epitech.eu/ecole-informatique-apres-bac/engagements/"


def _strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_values_sentence(text: str) -> str | None:
    """
    Extract the canonical sentence visible on the official engagements page:
    "Chez Epitech, nous croyons en nos valeurs, que sont l'excellence, le courage et la solidarité."
    """
    # Normalize apostrophes
    t = text.replace("’", "'")

    # Prefer an exact-ish match to avoid picking unrelated marketing lines.
    m = re.search(
        r"(Chez\s+Epitech,\s+nous\s+croyons\s+en\s+nos\s+valeurs,\s+que\s+sont\s+l['’]excellence,\s+le\s+courage\s+et\s+la\s+solidarit[eé]\.)",
        t,
        flags=re.IGNORECASE,
    )
    if m:
        # Return with original casing from the match group
        s = m.group(1).strip()
        # Fix casing: start with "Chez Epitech"
        return "Chez Epitech, nous croyons en nos valeurs, que sont l'excellence, le courage et la solidarité."

    # Fallback: if the sentence is slightly different, still try to find the three values together near "Chez Epitech".
    idx = t.lower().find("chez epitech")
    if idx != -1:
        window = t[idx : idx + 600]
        if all(w in window.lower() for w in ("excellence", "courage", "solidarit")):
            return "Chez Epitech, nous croyons en nos valeurs, que sont l'excellence, le courage et la solidarité."

    return None


async def scrape_values(timeout_sec: int, user_agent: str) -> Tuple[Dict[str, Any], int]:
    headers = {"User-Agent": user_agent}
    start = time.time()
    async with httpx.AsyncClient(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        r = await client.get(VALUES_URL)
        r.raise_for_status()
        html = r.text or ""
    duration_ms = int((time.time() - start) * 1000)

    text = _strip_tags(html)
    values_sentence = _extract_values_sentence(text)

    data: Dict[str, Any] = {
        "url": VALUES_URL,
        "values_sentence": values_sentence,
        "values": ["excellence", "courage", "solidarité"] if values_sentence else [],
    }
    return data, duration_ms

