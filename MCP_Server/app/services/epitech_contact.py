from __future__ import annotations

import re
from typing import Dict, List, Tuple

import httpx


CONTACT_URL = "https://www.epitech.eu/contact/"


_CITY_COUNTRY: Dict[str, str] = {
    # France (15)
    "Bordeaux": "France",
    "La Réunion": "France",
    "Lille": "France",
    "Lyon": "France",
    "Marseille": "France",
    "Montpellier": "France",
    "Moulins": "France",
    "Mulhouse": "France",
    "Nancy": "France",
    "Nantes": "France",
    "Nice": "France",
    "Paris": "France",
    "Rennes": "France",
    "Strasbourg": "France",
    "Toulouse": "France",
    # International (5)
    "Barcelone": "Espagne",
    "Berlin": "Allemagne",
    "Bruxelles": "Belgique",
    "Cotonou": "Bénin",
    "Madrid": "Espagne",
}


def _default_campus_url(city: str) -> str:
    # Note: Epitech international pages are often not city-specific.
    if city in ("Madrid", "Barcelone"):
        return "https://www.epitech-it.es/"
    if city == "Berlin":
        return "https://www.epitech-it.de/"
    if city == "Bruxelles":
        return "https://www.epitech-it.be/"
    if city == "Cotonou":
        return "https://epitech.bj/"
    if city == "La Réunion":
        return "https://www.epitech.eu/ecole-informatique-saint-andre-la-reunion/"

    slug = (
        city.lower()
        .replace(" ", "-")
        .replace("’", "")
        .replace("'", "")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ç", "c")
    )
    return f"https://www.epitech.eu/ecole-informatique-{slug}/"


def _extract_cities_from_text(text: str) -> List[str]:
    # Extract headings like "Epitech à Bordeaux"
    # We take the shortest city token after "Epitech à " up to newline/pipe.
    # This is robust against HTML changes because we operate on full page text.
    candidates = []
    pattern = re.compile(r"\bEpitech\s+à\s+([A-Za-zÀ-ÿ'’ -]+)", re.IGNORECASE)
    for m in pattern.finditer(text):
        raw = m.group(1).strip()
        raw = re.split(r"[\n\r\t|,]", raw)[0].strip()
        raw = raw.strip(" .;:!?\u00a0")
        # Normalize Reunion variants
        if raw.lower() in ("la reunion", "la réunion", "reunion", "réunion"):
            raw = "La Réunion"
        # Capitalize first letters but keep accents
        city = " ".join([w[:1].upper() + w[1:] for w in raw.split(" ") if w])
        candidates.append(city)
    return candidates


async def scrape_campuses(timeout_sec: int, user_agent: str) -> Tuple[List[Dict], int]:
    """
    Returns (campus_list, duration_ms)
    Output campus_list item schema matches what the backend expects.
    """
    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(timeout=timeout_sec, headers=headers, follow_redirects=True) as client:
        import time
        start = time.time()
        r = await client.get(CONTACT_URL)
        r.raise_for_status()
        text = r.text
        duration_ms = int((time.time() - start) * 1000)

    # 1) Preferred: extract from "Epitech à <Ville>" headings in the page text
    found = set()
    for city in _extract_cities_from_text(text):
        if city in _CITY_COUNTRY:
            found.add(city)

    # 2) Complement: also scan for any known city names present anywhere on the page.
    # This is needed because some cities appear in menus/lists without the exact "Epitech à" prefix.
    lower = text.lower()
    for city in _CITY_COUNTRY.keys():
        if city.lower() in lower:
            found.add(city)

    campuses = []
    for city in sorted(found):
        campuses.append(
            {
                "ville": city,
                "pays": _CITY_COUNTRY[city],
                "url": _default_campus_url(city),
                # Keep light; backend can display "Toutes formations"
                "formations_disponibles": [],
            }
        )

    return campuses, duration_ms

