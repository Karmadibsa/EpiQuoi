import scrapy

class CampusSpider(scrapy.Spider):
    name = "campus_spider"
    start_urls = [
        "https://www.epitech.eu/contact/",  # Pour les campus (Annuaire)
        #"https://www.epitech.eu/metiers-apres-ecole-informatique/",
        #"https://www.epitech.eu/formation-bachelor-ecole-informatique/" ,
        #"https://www.epitech.eu/formation-alternance/pre-msc-post-bac2/",
        #"https://www.epitech.eu/formation-alternance/master-of-science-post-bac3/"
    ]

    def parse(self, response):
        seen_items = set()  # Utiliser (url, ville) pour éviter les doublons
        seen_cities = set()
        seen_urls = set()  # Pour éviter de traiter plusieurs fois la même URL
        
        excluded_words = [
            "valeurs", "pédagogie", "engagements", "direction", 
            "groupe", "group", "associative", "bac", "après", "tech",
            "ionis", "education", "ancien", "alumni", "contact", "digital",
            "voir", "plus", "découvrir", "en savoir", "lire", "cliquez"
        ]

        # Liste des villes Epitech connues pour validation
        known_cities = {
            "paris", "lyon", "marseille", "toulouse", "nice", "nantes", "strasbourg",
            "montpellier", "bordeaux", "lille", "rennes", "nancy", "mulhouse",
            "moulins", "la réunion", "saint-andré", "abidjan", "cotonou",
            "berlin", "madrid", "barcelone", "bruxelles", "tirana"
        }

        # On garde notre logique de détection des pays qui marche bien
        for link in response.css('a'):
            url = link.css('::attr(href)').get()
            text = link.css('::text').get()
            
            if not url: continue
            
            # Normaliser l'URL (enlever les fragments, paramètres, etc.)
            url_clean = url.split('#')[0].split('?')[0]
            url_lower = url_clean.lower()
            # print(f"DEBUG: Checking {url_lower}")
            
            # On ignore explicitement toutes les pages "après-bac" qui ne sont PAS des campus physiques
            # Exemple : /ecole-informatique-apres-bac/..., pages pédagogie, engagements, etc.
            if "ecole-informatique-apres-bac" in url_lower or "apres-bac" in url_lower or "après-bac" in url_lower:
                continue
            
            # Skip si déjà vu
            if url_clean in seen_urls: continue
            
            # Détection basée sur l'URL (plus fiable que le texte)
            pays = None
            is_campus = False
            ville = None

            # Campus internationaux
            if ".es" in url_lower or "epitech-it.es" in url_lower:
                pays = "Espagne"
                is_campus = True
                if "madrid" in url_lower:
                    ville = "Madrid"
                elif "barcelone" in url_lower or "barcelona" in url_lower:
                    ville = "Barcelone"
                # Remove default to allow text detection for Madrid
            elif ".de" in url_lower or "epitech-it.de" in url_lower or "berlin" in url_lower:
                pays = "Allemagne"
                is_campus = True
                ville = "Berlin"
            elif ".be" in url_lower or "epitech-it.be" in url_lower or "bruxelles" in url_lower:
                pays = "Belgique"
                is_campus = True
                ville = "Bruxelles"
            elif ".bj" in url_lower or "epitech.bj" in url_lower or "cotonou" in url_lower:
                pays = "Bénin"
                is_campus = True
                ville = "Cotonou"
            elif "tirana" in url_lower or "albanie" in url_lower:
                pays = "Albanie"
                is_campus = True
                ville = "Tirana"
            # Campus français - patterns plus larges
            elif "/campus-" in url_lower or "/ecole-informatique-" in url_lower:
                pays = "France"
                is_campus = True
                # Extraire le nom de la ville depuis l'URL
                if "/campus-" in url_lower:
                    ville_part = url_lower.split("/campus-")[-1].split("/")[0]
                elif "/ecole-informatique-" in url_lower:
                    ville_part = url_lower.split("/ecole-informatique-")[-1].split("/")[0]
                else:
                    ville_part = None
                
                if ville_part:
                    # Nettoyer et capitaliser
                    ville = ville_part.replace("-", " ").title()
                    # Cas spéciaux
                    if "saint-andre" in ville_part or "reunion" in ville_part:
                        ville = "La Réunion"
                    elif "abidjan" in ville_part:
                        pays = "Côte d'Ivoire"
                        ville = "Abidjan"

            # Si pas de ville depuis l'URL, essayer depuis le texte
            if is_campus and not ville and text:
                clean_text = text.strip()
                text_lower = clean_text.lower()
                
                # Filtrer les mots exclus
                if any(word in text_lower for word in excluded_words): 
                    continue
                
                # Vérifier si c'est une ville connue
                if clean_text.lower() in known_cities or any(city in text_lower for city in known_cities):
                    ville = clean_text
                elif len(clean_text) > 2 and len(clean_text) < 30:
                    # Accepter si ça ressemble à un nom de ville
                    ville = clean_text

            # Si on a détecté un campus valide
            if is_campus and ville:
                print(f"DEBUG: Found Campus {ville} at {url_clean}")
                # Utiliser (url, ville) comme clé unique
                item_key = (url_clean, ville)
                if item_key not in seen_items:
                    seen_items.add(item_key)
                    seen_cities.add(ville.lower())
                    # On suit le lien pour aller chercher les détails
                    yield response.follow(
                        url_clean, 
                        callback=self.parse_details, 
                        cb_kwargs={'ville': ville, 'pays': pays, 'url_base': url_clean},
                        dont_filter=True
                    )

    def parse_details(self, response, ville, pays, url_base):
        """Récupère les formations via Titres ET Liens (pour avoir les MSc/MBA)"""
        
        formations_set = set() # Pour éviter les doublons
        formations_list = []
        
        # J'ai ajouté 'mba', 'pre-msc' suite à ton image
        keywords = ["campus","programme", "bachelor", "master", "msc", "cursus", "formation", "bootcamp", "coding academy", "mba"]
        
        # STRATEGIE 1 : Les Titres (H1-H4)
        for title in response.css('h1, h2, h3, h4'):
            txt = title.css('::text').get()
            if txt and any(k in txt.lower() for k in keywords):
                clean = txt.strip()
                if clean not in formations_set and len(clean) < 100:
                    formations_set.add(clean)
                    formations_list.append({"nom": clean, "type": "Titre Principal"})

        # STRATEGIE 2 : Les Liens/Menus (C'est ça qui va attraper ton image)
        # On cherche tous les liens <a> ou items de liste <li> contenant les mots clés
        for item in response.css('a::text, li::text'):
            txt = item.get()
            if txt and any(k in txt.lower() for k in keywords):
                clean = txt.strip()
                # On filtre pour éviter les phrases trop longues (on veut juste le nom du programme)
                if clean not in formations_set and 5 < len(clean) < 60:
                    formations_set.add(clean)
                    formations_list.append({"nom": clean, "type": "Programme Spécialisé"})

        # Sécurité : Si vide, message par défaut
        if not formations_list:
            formations_list.append({"nom": "Formations générales Epitech (voir site)", "type": "Général"})

        yield {
            "ville": ville,
            "pays": pays,
            "url": url_base,
            "formations_disponibles": formations_list
        }