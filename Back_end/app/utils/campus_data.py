"""Campus data and utilities."""

from typing import Dict, Optional, Tuple, Any

# Données des campus Epitech avec coordonnées
CAMPUSES: Dict[str, Dict[str, Any]] = {
    "Paris": {
        "country": "France",
        "zip": "94270",
        "addr": "24 rue Pasteur, 94270 Le Kremlin-Bicêtre",
        "coords": (48.8156, 2.3631),
        "email": "paris@epitech.eu",
        "phone": "01 44 08 00 60"
    },
    "Bordeaux": {
        "country": "France",
        "zip": "33000",
        "addr": "81-89 Rue du Jardin public, 33000 Bordeaux",
        "coords": (44.8432, -0.5756),
        "email": "bordeaux@epitech.eu",
        "phone": "05 64 13 05 84"
    },
    "Lille": {
        "country": "France",
        "zip": "59000",
        "addr": "5-9 Rue du Palais Rihour, 59000 Lille",
        "coords": (50.6359, 3.0617),
        "email": "lille@epitech.eu",
        "phone": "03 74 09 16 24"
    },
    "Lyon": {
        "country": "France",
        "zip": "69000",
        "addr": "86 Boulevard Marius Vivier Merle, 69003 Lyon",
        "coords": (45.7597, 4.8584),
        "email": "lyon@epitech.eu",
        "phone": "04 28 29 33 25"
    },
    "Marseille": {
        "country": "France",
        "zip": "13000",
        "addr": "21 Rue Marc Donadille, 13013 Marseille",
        "coords": (43.3444, 5.4243),
        "email": "marseille@epitech.eu",
        "phone": "04 84 89 13 54"
    },
    "Montpellier": {
        "country": "France",
        "zip": "34000",
        "addr": "16 Boulevard des Arceaux, 34000 Montpellier",
        "coords": (43.6095, 3.8687),
        "email": "montpellier@epitech.eu",
        "phone": "04 11 93 17 52"
    },
    "Nantes": {
        "country": "France",
        "zip": "44000",
        "addr": "18 Rue Flandres-Dunkerque, 44000 Nantes",
        "coords": (47.2156, -1.5552),
        "email": "nantes@epitech.eu",
        "phone": "02 85 52 28 71"
    },
    "Nancy": {
        "country": "France",
        "zip": "54000",
        "addr": "80 Rue Saint-Georges, 54000 Nancy",
        "coords": (48.6923, 6.1848),
        "email": "nancy@epitech.eu",
        "phone": "03 72 47 11 50"
    },
    "Nice": {
        "country": "France",
        "zip": "06000",
        "addr": "13 Rue Saint-François de Paule, 06300 Nice",
        "coords": (43.6961, 7.2718),
        "email": "nice@epitech.eu",
        "phone": "04 22 13 32 66"
    },
    "Rennes": {
        "country": "France",
        "zip": "35000",
        "addr": "19 Rue Jean-Marie Huchet, 35000 Rennes",
        "coords": (48.1130, -1.6738),
        "email": "rennes@epitech.eu",
        "phone": "02 57 22 08 54"
    },
    "Strasbourg": {
        "country": "France",
        "zip": "67000",
        "addr": "4 Rue du Dôme, 67000 Strasbourg",
        "coords": (48.5831, 7.7479),
        "email": "strasbourg@epitech.eu",
        "phone": "03 67 10 28 83"
    },
    "Toulouse": {
        "country": "France",
        "zip": "31000",
        "addr": "40 Boulevard de la Marquette, 31000 Toulouse",
        "coords": (43.6125, 1.4287),
        "email": "toulouse@epitech.eu",
        "phone": "05 82 95 79 93"
    },
    "Barcelone": {
        "country": "Espagne",
        "zip": "08005",
        "addr": "Carrer de Joan Miró, 21, 08005 Barcelona, Espagne",
        "coords": (41.3909, 2.1940),
        "email": "barcelona@epitech.eu",
        "phone": "+34 937 97 88 14"
    },
    "Berlin": {
        "country": "Allemagne",
        "zip": "10623",
        "addr": "Fasanenstraße 86, 10623 Berlin, Allemagne",
        "coords": (52.5084, 13.3293),
        "email": "berlin@epitech.eu",
        "phone": "+49 30 982 892 41"
    },
    "Bruxelles": {
        "country": "Belgique",
        "zip": "1000",
        "addr": "Rue Royale 196, 1000 Bruxelles, Belgique",
        "coords": (50.8523, 4.3651),
        "email": "brussels@epitech.eu",
        "phone": "+32 2 315 22 82"
    },
    "Cotonou": {
        "country": "Benin",
        "zip": "00000",
        "addr": "Campus Sèmè One, Cotonou, Bénin",
        "coords": (6.3653, 2.4183),
        "email": "cotonou@epitech.eu",
        "phone": "+229 69 07 89 02"
    },
}

CITY_ALIASES: Dict[str, str] = {
    "barcelona": "Barcelone",
    "barna": "Barcelone",
    "brussels": "Bruxelles",
    "brussel": "Bruxelles",
    "berlim": "Berlin",
}


def get_campus_info(city: str) -> Optional[Dict[str, Any]]:
    """Get campus information by city name."""
    return CAMPUSES.get(city)


def get_all_campus_names() -> list[str]:
    """Get list of all campus city names."""
    return list(CAMPUSES.keys())


def format_campus_list() -> str:
    """Format all campuses into a string for system prompts."""
    formatted = ""
    for city, data in CAMPUSES.items():
        formatted += (
            f"- {city.upper()}: {data['addr']} "
            f"(Tel: {data.get('phone', 'N/A')}, "
            f"Email: {data.get('email', 'N/A')})\n"
        )
    return formatted
