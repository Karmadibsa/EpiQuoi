from __future__ import annotations

import html as _html
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


def _html_to_text_lines(raw_html: str) -> List[str]:
    """
    Convert HTML to a reasonably stable text-lines representation using only stdlib + regex.
    We intentionally avoid relying on specific DOM structures.
    """
    if not raw_html:
        return []

    s = raw_html
    # Remove scripts/styles
    s = re.sub(r"(?is)<script[^>]*>.*?</script>", "\n", s)
    s = re.sub(r"(?is)<style[^>]*>.*?</style>", "\n", s)
    # Turn common block separators into newlines
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|h1|h2|h3|h4|section|article)>", "\n", s)
    # Drop remaining tags
    s = re.sub(r"(?is)<[^>]+>", "", s)
    # Unescape HTML entities
    s = _html.unescape(s)
    # Normalize whitespace
    s = s.replace("\r", "\n")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    lines = [ln.strip(" \t\u00a0") for ln in s.split("\n")]
    return [ln for ln in lines if ln]


def _extract_contact_blocks(lines: List[str]) -> Dict[str, Dict[str, object]]:
    """
    Extract per-campus contact blocks from the contact page text.
    Returns: { city: { "address_lines": [...], "email": str|None, "phone": str|None } }
    """
    # Headings appear as "Epitech à <Ville>"
    heading_re = re.compile(r"^Epitech\s+à\s+(.+)$", re.IGNORECASE)
    email_re = re.compile(r"[A-Z0-9._%+-]+@(?:[A-Z0-9-]+\.)+[A-Z]{2,}", re.IGNORECASE)
    # Phone: keep permissive (FR + international), but avoid catching years
    phone_re = re.compile(r"^(?:\+?\d{1,3}\s*)?(?:\(?0?\d\)?[\s.\-]*){6,}\d$")

    # Collect indices of headings
    heading_idx: List[Tuple[int, str]] = []
    for i, ln in enumerate(lines):
        m = heading_re.match(ln)
        if not m:
            continue
        city_raw = m.group(1).strip()
        city_raw = city_raw.strip(" -–—:•")
        # Normalize Reunion variants
        if city_raw.lower() in ("la reunion", "la réunion", "reunion", "réunion"):
            city_raw = "La Réunion"
        heading_idx.append((i, city_raw))

    blocks: Dict[str, Dict[str, object]] = {}
    for j, (start_i, city) in enumerate(heading_idx):
        end_i = heading_idx[j + 1][0] if j + 1 < len(heading_idx) else len(lines)
        chunk = lines[start_i + 1 : end_i]
        if not chunk:
            continue

        email = None
        phone = None
        addr_lines: List[str] = []

        for ln in chunk:
            if email is None and email_re.search(ln):
                # Prefer campus emails; ignore generic placeholders if present
                found = email_re.search(ln).group(0)
                email = found
                continue

            # Phone lines can appear without "tel:"; keep first that looks like a phone.
            if phone is None and (phone_re.match(ln) or (ln.startswith("+") and any(ch.isdigit() for ch in ln))):
                phone = ln
                continue

            # Address lines: keep early lines until we hit obvious non-address parts
            low = ln.lower()
            if any(k in low for k in ("contacts", "réclam", "reclam", "journées portes ouvertes", "agenda", "fermer")):
                continue
            if email_re.search(ln):
                continue
            if phone_re.match(ln):
                continue
            # Avoid keeping menu items like "Documentation / Candidature"
            if len(ln) <= 2:
                continue
            addr_lines.append(ln)

        # Heuristic: address is typically 2-4 lines near the beginning; drop trailing noise if too long
        if len(addr_lines) > 6:
            addr_lines = addr_lines[:6]

        # Only store if city is known
        blocks[city] = {
            "address_lines": addr_lines,
            "email": email,
            "phone": phone,
        }

    return blocks


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
        raw_html = r.text
        duration_ms = int((time.time() - start) * 1000)

    # 1) Preferred: extract from "Epitech à <Ville>" headings in the page text
    found = set()
    for city in _extract_cities_from_text(raw_html):
        if city in _CITY_COUNTRY:
            found.add(city)

    # 2) Complement: also scan for any known city names present anywhere on the page.
    # This is needed because some cities appear in menus/lists without the exact "Epitech à" prefix.
    lower = raw_html.lower()
    for city in _CITY_COUNTRY.keys():
        if city.lower() in lower:
            found.add(city)

    # 3) Extract contact details (address/email/phone) per campus from the same page
    lines = _html_to_text_lines(raw_html)
    contact_blocks = _extract_contact_blocks(lines)

    campuses = []
    for city in sorted(found):
        contact = contact_blocks.get(city, {})
        campuses.append(
            {
                "ville": city,
                "pays": _CITY_COUNTRY[city],
                "url": _default_campus_url(city),
                "contact_source_url": CONTACT_URL,
                "adresse_lignes": contact.get("address_lines") if isinstance(contact, dict) else [],
                "email": contact.get("email") if isinstance(contact, dict) else None,
                "telephone": contact.get("phone") if isinstance(contact, dict) else None,
                # Keep light; backend can display "Toutes formations"
                "formations_disponibles": [],
            }
        )

    return campuses, duration_ms

