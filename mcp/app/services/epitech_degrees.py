from __future__ import annotations

import asyncio
import re
import time
from html import unescape
from typing import Any, Dict, List, Tuple

import httpx


# Official program pages (provided list) – used as the source of truth.
DEGREES_CATALOG: List[Dict[str, Any]] = [
    {
        "nom": "Programme Grande École",
        "categorie": "Diplôme",
        "niveau": "Bac+5",
        "pages": [
            "https://www.epitech.eu/programme-grande-ecole-informatique/",
            "https://www.epitech.eu/programme-grande-ecole-informatique/etudier-a-letranger/",
        ],
    },
    {
        "nom": "Programme Bachelor",
        "categorie": "Diplôme",
        "niveau": "Bac+3",
        "pages": [
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/",
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/intelligence-artificielle/",
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/cybersecurite/",
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/cloud-web3/",
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/tech-business-management/",
            "https://www.epitech.eu/formation-bachelor-ecole-informatique/developpeur-full-stack/",
        ],
    },
    {
        "nom": "Programme Master of Science",
        "categorie": "Spécialisation",
        "niveau": "Post Bac+2/Bac+3",
        "pages": [
            "https://www.epitech.eu/formation-alternance/pre-msc-post-bac2/",
            "https://www.epitech.eu/formation-alternance/master-of-science-post-bac3/",
            "https://www.epitech.eu/formation-alternance/master-of-science-cybersecurite/",
            "https://www.epitech.eu/formation-alternance/master-of-science-cloud/",
            "https://www.epitech.eu/formation-alternance/master-of-science-big-data/",
            "https://www.epitech.eu/formation-alternance/master-of-science-realite-virtuelle/",
            "https://www.epitech.eu/formation-alternance/master-of-science-intelligence-artificielle/",
            "https://www.epitech.eu/formation-alternance/master-of-science-robotique-iot/",
        ],
    },
    {
        "nom": "MBA",
        "categorie": "MBA",
        "niveau": "Post Bac+3",
        "pages": [
            "https://www.epitech.eu/formation-alternance/mba-strategic-project-management-entrepreneurship/",
            "https://www.epitech.eu/formation-alternance/mba-fintech-strategies-financieres/",
            "https://www.epitech.eu/formation-alternance/mba-marketing-influence/",
            "https://www.epitech.eu/formation-alternance/mba-intelligence-artificielle-transformation-organisation/",
            "https://www.epitech.eu/formation-alternance/mba-data-protection-securite/",
            "https://www.epitech.eu/formation-alternance/mba-digitalisation-de-la-fonction-rh/",
            "https://www.epitech.eu/formation-alternance/mba-sante-ia-iot/",
            "https://www.epitech.eu/formation-alternance/mba-data-science-business-intelligence/",
            "https://www.epitech.eu/formation-alternance/mba-luxe-retail-tech/",
        ],
    },
]


def _strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_meta(html: str, name: str) -> str | None:
    # <meta name="description" content="...">
    m = re.search(
        rf'(?is)<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        html,
    )
    return unescape(m.group(1)).strip() if m else None


def _extract_og(html: str, prop: str) -> str | None:
    # <meta property="og:title" content="...">
    m = re.search(
        rf'(?is)<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        html,
    )
    return unescape(m.group(1)).strip() if m else None


def _extract_title(html: str) -> str | None:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if not m:
        return None
    return unescape(re.sub(r"\s+", " ", m.group(1))).strip()


def _extract_h1(html: str) -> str | None:
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    if not m:
        return None
    return unescape(_strip_tags(m.group(1)))


def _short_snippet(text: str, max_len: int = 320) -> str | None:
    if not text:
        return None
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= max_len:
        return t
    cut = t[:max_len]
    # cut at sentence boundary if possible
    m = re.search(r"[.!?]\s", cut)
    if m:
        return cut[: m.end()].strip()
    return cut.strip() + "…"


def _extract_duration_hints(text: str) -> List[str]:
    """
    Extract short duration hints like "1 an", "2 ans", "6 mois" from page text.
    We keep it conservative and return up to a few unique matches.
    """
    if not text:
        return []
    lower = text.lower()
    patterns = [
        r"\b\d+\s*(?:an|ans|année|années)\b",
        r"\b\d+\s*(?:mois)\b",
    ]
    found: List[str] = []
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, lower):
            s = m.group(0).strip()
            if s in seen:
                continue
            seen.add(s)
            found.append(s)
            if len(found) >= 6:
                return found
    return found


async def scrape_degrees(timeout_sec: int, user_agent: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns (programs, duration_ms)

    Output schema:
      [
        {
          nom, categorie, niveau,
          pages: [{url, title, h1, description, snippet}]
        }, ...
      ]
    """
    headers = {"User-Agent": user_agent}
    start = time.time()

    async with httpx.AsyncClient(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        sem = asyncio.Semaphore(8)

        async def fetch(url: str) -> Dict[str, Any]:
            async with sem:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    html = r.text or ""
                    text = _strip_tags(html)
                    return {
                        "url": url,
                        "title": _extract_og(html, "og:title") or _extract_title(html),
                        "h1": _extract_h1(html),
                        "description": _extract_meta(html, "description") or _extract_og(html, "og:description"),
                        "snippet": _short_snippet(text, 360),
                        "duration_hints": _extract_duration_hints(text),
                    }
                except Exception as e:
                    return {"url": url, "error": str(e)}

        out: List[Dict[str, Any]] = []
        for program in DEGREES_CATALOG:
            urls = program.get("pages", [])
            page_items = await asyncio.gather(*[fetch(u) for u in urls])
            out.append(
                {
                    "nom": program["nom"],
                    "categorie": program["categorie"],
                    "niveau": program["niveau"],
                    "pages": page_items,
                }
            )

    duration_ms = int((time.time() - start) * 1000)
    return out, duration_ms

