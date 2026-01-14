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
        seen_cities = set()
        
        excluded_words = [
            "valeurs", "pédagogie", "engagements", "direction", 
            "groupe", "group", "associative", "bac", "après", "tech",
            "ionis", "education", "ancien", "alumni", "contact", "digital"
        ]

        # On garde notre logique de détection des pays qui marche bien
        for link in response.css('a'):
            url = link.css('::attr(href)').get()
            text = link.css('::text').get()
            
            if not url or not text: continue

            clean_text = text.strip()
            text_lower = clean_text.lower()
            url_lower = url.lower()

            if any(word in text_lower for word in excluded_words): continue
            
            pays = None
            is_campus = False

            if ".es" in url_lower or "madrid" in text_lower or "barcelone" in text_lower or "spain" in url_lower:
                pays = "Espagne"
                is_campus = True
            elif ".de" in url_lower or "berlin" in text_lower or "germany" in url_lower:
                pays = "Allemagne"
                is_campus = True
            elif ".be" in url_lower or "bruxelles" in text_lower or "belgium" in url_lower:
                pays = "Belgique"
                is_campus = True
            elif ".bj" in url_lower or "cotonou" in text_lower or "benin" in url_lower:
                pays = "Bénin"
                is_campus = True
            elif "tirana" in text_lower or "albanie" in url_lower:
                pays = "Albanie"
                is_campus = True
            elif "/campus-" in url_lower or "/ecole-" in url_lower:
                if not pays: 
                    pays = "France"
                    is_campus = True

            if is_campus and len(clean_text) > 2 and len(clean_text) < 30:
                if clean_text not in seen_cities:
                    seen_cities.add(clean_text)
                    # On suit le lien pour aller chercher les détails
                    yield response.follow(
                        url, 
                        callback=self.parse_details, 
                        cb_kwargs={'ville': clean_text, 'pays': pays, 'url_base': url}
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