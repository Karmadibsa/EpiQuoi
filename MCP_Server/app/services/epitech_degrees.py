from __future__ import annotations

import re
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import httpx


EPITECH_BASE_URL = "https://www.epitech.eu/"

# Heuristic keywords to discover and parse program pages.
_DISCOVERY_KEYWORDS = (
    "formation",
    "formations",
    "programme",
    "programmes",
    "bachelor",
    "msc",
    "master-of-science",
    "master of science",
    "coding-academy",
    "coding academy",
    "web@cadémie",
    "web@academie",
    "webacademy",
    "grande-ecole",
    "grande école",
)


def _is_internal_epitech_url(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in ("http", "https") and p.netloc.endswith("epitech.eu")


def _extract_links(html: str, base_url: str) -> List[str]:
    # Basic href extraction (keeps this service dependency-free).
    links = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        abs_url = urljoin(base_url, href)
        if _is_internal_epitech_url(abs_url):
            links.append(abs_url)
    # Deduplicate while preserving order.
    seen = set()
    out = []
    for u in links:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _detect_programs_from_text(text: str, best_url_by_program: Dict[str, str]) -> List[Dict]:
    """
    Extract a stable, compact list of degree/program types.
    This is intentionally conservative: we prefer returning fewer correct items rather than noisy marketing items.
    """
    t = text.lower()

    def has(*needles: str) -> bool:
        return any(n.lower() in t for n in needles)

    programs: List[Dict] = []

    if has("programme grande école", "programme grande ecole", "grande école", "grande ecole", "pge"):
        programs.append(
            {
                "nom": "Programme Grande École",
                "categorie": "Diplôme",
                "niveau": "Bac+5",
                "url": best_url_by_program.get("Programme Grande École"),
            }
        )

    if has("bachelor"):
        programs.append(
            {
                "nom": "Bachelor",
                "categorie": "Diplôme",
                "niveau": "Bac+3",
                "url": best_url_by_program.get("Bachelor"),
            }
        )

    if has("msc", "master of science", "master-of-science", "msc pro"):
        programs.append(
            {
                "nom": "MSc Pro / Master of Science",
                "categorie": "Spécialisation",
                "niveau": "Bac+5",
                "url": best_url_by_program.get("MSc Pro / Master of Science"),
            }
        )

    if has("coding academy", "coding-academy"):
        programs.append(
            {
                "nom": "Coding Academy",
                "categorie": "Reconversion",
                "niveau": None,
                "url": best_url_by_program.get("Coding Academy"),
            }
        )

    if has("web@cadémie", "web@academie", "webacademy"):
        programs.append(
            {
                "nom": "Web@cadémie",
                "categorie": "Alternance / Web",
                "niveau": None,
                "url": best_url_by_program.get("Web@cadémie"),
            }
        )

    return programs


async def scrape_degrees(
    timeout_sec: int,
    user_agent: str,
    max_pages: int = 20,
    seed_urls: List[str] | None = None,
) -> Tuple[List[Dict], int]:
    """
    Returns (degrees_list, duration_ms)

    Note: we keep this dependency-free. The strategy is:
    - Fetch a few seed pages
    - Discover internal links likely related to programs/formations
    - Fetch up to max_pages candidates and infer which program types exist
    """
    seed_urls = seed_urls or [
        EPITECH_BASE_URL,
        urljoin(EPITECH_BASE_URL, "formations/"),
        urljoin(EPITECH_BASE_URL, "programme/"),
        urljoin(EPITECH_BASE_URL, "programmes/"),
        urljoin(EPITECH_BASE_URL, "admission/"),
    ]

    headers = {"User-Agent": user_agent}
    start = time.time()

    async with httpx.AsyncClient(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        pages_text: List[Tuple[str, str]] = []
        discovered: List[str] = []

        # 1) Seed fetch
        for u in seed_urls:
            try:
                r = await client.get(u)
                if r.status_code >= 400:
                    continue
                html = r.text or ""
                pages_text.append((u, html))
                discovered.extend(_extract_links(html, u))
            except Exception:
                continue

        # 2) Candidate pages (filtered by keywords)
        candidates = []
        for u in discovered:
            lu = u.lower()
            if any(k in lu for k in _DISCOVERY_KEYWORDS):
                candidates.append(u)
        # Deduplicate
        seen = set()
        candidates = [u for u in candidates if not (u in seen or seen.add(u))]

        # 3) Fetch candidates (bounded)
        for u in candidates[:max_pages]:
            try:
                r = await client.get(u)
                if r.status_code >= 400:
                    continue
                pages_text.append((u, r.text or ""))
            except Exception:
                continue

    duration_ms = int((time.time() - start) * 1000)

    # Build best URLs per program based on URL hints
    best_url_by_program: Dict[str, str] = {}
    for url, html in pages_text:
        lu = url.lower()
        # Simple URL-based preference mapping
        if "grande" in lu or "ecole" in lu or "pge" in lu:
            best_url_by_program.setdefault("Programme Grande École", url)
        if "bachelor" in lu:
            best_url_by_program.setdefault("Bachelor", url)
        if "msc" in lu or "master" in lu:
            best_url_by_program.setdefault("MSc Pro / Master of Science", url)
        if "coding" in lu and "academy" in lu:
            best_url_by_program.setdefault("Coding Academy", url)
        if "web" in lu and ("academ" in lu or "wac" in lu):
            best_url_by_program.setdefault("Web@cadémie", url)

        # Some pages may contain clear headings; allow content-based fallback too.
        txt = _normalize_space(re.sub(r"<[^>]+>", " ", html))
        lt = txt.lower()
        if "programme grande" in lt or "grande école" in lt or "grande ecole" in lt:
            best_url_by_program.setdefault("Programme Grande École", url)
        if "bachelor" in lt:
            best_url_by_program.setdefault("Bachelor", url)
        if "master of science" in lt or "msc" in lt:
            best_url_by_program.setdefault("MSc Pro / Master of Science", url)
        if "coding academy" in lt:
            best_url_by_program.setdefault("Coding Academy", url)
        if "web@cadémie" in lt or "web@academie" in lt:
            best_url_by_program.setdefault("Web@cadémie", url)

    # Infer programs from concatenated text
    combined_text = "\n".join(_normalize_space(re.sub(r"<[^>]+>", " ", html)) for _, html in pages_text)
    degrees = _detect_programs_from_text(combined_text, best_url_by_program)

    # If discovery fails (site changes, blocked, etc.), provide a safe minimal fallback list.
    if not degrees:
        degrees = [
            {"nom": "Programme Grande École", "categorie": "Diplôme", "niveau": "Bac+5", "url": None},
            {"nom": "MSc Pro / Master of Science", "categorie": "Spécialisation", "niveau": "Bac+5", "url": None},
            {"nom": "Coding Academy", "categorie": "Reconversion", "niveau": None, "url": None},
        ]

    return degrees, duration_ms

