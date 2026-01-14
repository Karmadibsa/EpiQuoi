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
        seen_urls = set()  # Utiliser les URLs pour éviter les doublons, pas le texte
        seen_cities = set()
        
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

        print(f"🔍 [Scraper] Analyse de la page /contact/ pour détecter les campus...")
        
        # STRATEGIE 1 : Scraper depuis les sections "Epitech à [Ville]" visibles sur la page
        # Ces sections contiennent directement les infos (adresse, email, tel)
        
        # Méthode améliorée : chercher tous les textes contenant "Epitech à" avec XPath plus robuste
        # Utiliser .//text() pour trouver le texte même dans les enfants
        campus_texts = response.xpath('//text()[contains(., "Epitech à") or contains(., "Epitech en")]')
        
        for text_node in campus_texts:
            full_text = text_node.get()
            if not full_text: continue
            
            text_lower = full_text.lower().strip()
            
            # Extraire la ville
            ville = None
            pays = "France"
            
            if "epitech à" in text_lower:
                # Extraire la ville après "Epitech à"
                parts = text_lower.split("epitech à")
                if len(parts) > 1:
                    ville_part = parts[-1].strip().split()[0]
                    # Nettoyer (enlever la ponctuation)
                    ville_part = ville_part.strip('.,;:!?')
                    if ville_part:
                        ville = ville_part.title()
            elif "epitech en" in text_lower:
                pays_part = text_lower.split("epitech en")[-1].strip().split()[0]
                pays_part = pays_part.strip('.,;:!?')
                if pays_part == "france":
                    continue  # On gère les villes françaises via les liens
                else:
                    pays = pays_part.title()
            
            if ville and ville.lower() in known_cities:
                # Cas spéciaux
                if "réunion" in text_lower or ville.lower() == "la réunion":
                    ville = "La Réunion"
                
                if ville.lower() not in seen_cities:
                    seen_cities.add(ville.lower())
                    
                    # Déterminer le pays
                    if ville.lower() in ["berlin"]:
                        pays = "Allemagne"
                    elif ville.lower() in ["madrid", "barcelone"]:
                        pays = "Espagne"
                    elif ville.lower() in ["bruxelles"]:
                        pays = "Belgique"
                    elif ville.lower() in ["cotonou"]:
                        pays = "Bénin"
                    elif ville.lower() in ["tirana"]:
                        pays = "Albanie"
                    
                    # Chercher le lien associé dans l'élément parent ou proche
                    parent = text_node.xpath('./ancestor::*[1]').get()
                    link = None
                    if parent:
                        # Chercher un lien dans le parent ou ses enfants
                        link_elem = text_node.xpath('./ancestor::*[1]//a/@href').get()
                        if link_elem:
                            link = link_elem
                    
                    # Si pas de lien dans le parent, chercher un lien qui contient le nom de la ville
                    if not link:
                        link = response.css(f'a[href*="{ville.lower().replace(" ", "-")}"]::attr(href)').get()
                    if not link:
                        # Chercher dans tous les liens de la page
                        for link_elem in response.css('a'):
                            link_text = link_elem.css('::text').get()
                            link_href = link_elem.css('::attr(href)').get()
                            if link_text and ville.lower() in link_text.lower():
                                link = link_href
                                break
                    
                    # Construire l'URL par défaut si pas de lien trouvé
                    if not link:
                        if ville.lower() == "madrid":
                            url_clean = "https://www.epitech-it.es/"
                        elif ville.lower() == "barcelone":
                            url_clean = "https://www.epitech-it.es/"
                        elif ville.lower() == "berlin":
                            url_clean = "https://www.epitech-it.de/"
                        elif ville.lower() == "bruxelles":
                            url_clean = "https://www.epitech-it.be/"
                        elif ville.lower() == "cotonou":
                            url_clean = "https://epitech.bj/"
                        elif ville.lower() == "la réunion" or ville.lower() == "saint-andré":
                            url_clean = "https://www.epitech.eu/ecole-informatique-saint-andre-la-reunion/"
                        else:
                            # Pour les villes françaises, construire l'URL standard
                            ville_slug = ville.lower().replace(" ", "-").replace("é", "e").replace("è", "e")
                            url_clean = f"https://www.epitech.eu/ecole-informatique-{ville_slug}/"
                    else:
                        url_clean = link.split('#')[0].split('?')[0]
                        # Si c'est un lien relatif, le convertir en absolu
                        if url_clean.startswith('/'):
                            url_clean = f"https://www.epitech.eu{url_clean}"
                    
                    if url_clean not in seen_urls:
                        seen_urls.add(url_clean)
                        print(f"   ✓ Campus détecté: {ville} ({pays}) -> {url_clean}")
                        yield response.follow(
                            url_clean,
                            callback=self.parse_details,
                            cb_kwargs={'ville': ville, 'pays': pays, 'url_base': url_clean},
                            dont_filter=True
                        )

        # STRATEGIE 1.5 : Extraire les villes depuis les titres de sections (h2, h3, h4, etc.)
        # Chercher les titres qui contiennent "Epitech à [Ville]"
        for title in response.css('h1, h2, h3, h4, h5, .campus-title, [class*="campus"]'):
            title_text = title.css('::text').get()
            if not title_text: continue
            
            title_lower = title_text.lower().strip()
            if "epitech à" in title_lower:
                ville_part = title_lower.split("epitech à")[-1].strip().split()[0]
                ville_part = ville_part.strip('.,;:!?')
                if ville_part and ville_part.lower() in known_cities:
                    ville = ville_part.title()
                    if "réunion" in title_lower:
                        ville = "La Réunion"
                    
                    if ville.lower() not in seen_cities:
                        seen_cities.add(ville.lower())
                        pays = "France"
                        if ville.lower() in ["berlin"]:
                            pays = "Allemagne"
                        elif ville.lower() in ["madrid", "barcelone"]:
                            pays = "Espagne"
                        elif ville.lower() in ["bruxelles"]:
                            pays = "Belgique"
                        elif ville.lower() in ["cotonou"]:
                            pays = "Bénin"
                        
                        # Chercher un lien dans le titre ou proche
                        link = title.css('a::attr(href)').get()
                        if not link:
                            link = title.xpath('.//a/@href').get()
                        if not link:
                            link = response.css(f'a[href*="{ville.lower().replace(" ", "-")}"]::attr(href)').get()
                        
                        if not link:
                            # URL par défaut
                            if ville.lower() == "madrid":
                                url_clean = "https://www.epitech-it.es/"
                            elif ville.lower() == "barcelone":
                                url_clean = "https://www.epitech-it.es/"
                            elif ville.lower() == "berlin":
                                url_clean = "https://www.epitech-it.de/"
                            elif ville.lower() == "bruxelles":
                                url_clean = "https://www.epitech-it.be/"
                            elif ville.lower() == "cotonou":
                                url_clean = "https://epitech.bj/"
                            elif ville.lower() == "la réunion":
                                url_clean = "https://www.epitech.eu/ecole-informatique-saint-andre-la-reunion/"
                            else:
                                ville_slug = ville.lower().replace(" ", "-").replace("é", "e").replace("è", "e")
                                url_clean = f"https://www.epitech.eu/ecole-informatique-{ville_slug}/"
                        else:
                            url_clean = link.split('#')[0].split('?')[0]
                            if url_clean.startswith('/'):
                                url_clean = f"https://www.epitech.eu{url_clean}"
                        
                        if url_clean not in seen_urls:
                            seen_urls.add(url_clean)
                            print(f"   ✓ Campus détecté (titre): {ville} ({pays}) -> {url_clean}")
                            yield response.follow(
                                url_clean,
                                callback=self.parse_details,
                                cb_kwargs={'ville': ville, 'pays': pays, 'url_base': url_clean},
                                dont_filter=True
                            )

        # STRATEGIE 2 : Scraper depuis les liens (méthode originale améliorée)
        print(f"   🔗 Analyse des liens pour détecter les campus...")
        link_count = 0
        for link in response.css('a'):
            url = link.css('::attr(href)').get()
            text = link.css('::text').get()
            
            if not url: continue
            
            # Normaliser l'URL (enlever les fragments, paramètres, etc.)
            url_clean = url.split('#')[0].split('?')[0]
            url_lower = url_clean.lower()
            
            # Filtrer les URLs externes (Google, Facebook, Twitter, etc.) - ne garder que les URLs Epitech
            external_domains = ["google.com", "facebook.com", "twitter.com", "linkedin.com", "instagram.com", 
                               "youtube.com", "tiktok.com", "snapchat.com", "mailto:", "tel:", "javascript:"]
            if any(domain in url_lower for domain in external_domains):
                continue
            
            # Ne garder que les URLs qui pointent vers epitech.eu, epitech-it.*, epitech.bj, etc.
            if not any(domain in url_lower for domain in ["epitech.eu", "epitech-it.", "epitech.bj"]):
                # Si ce n'est pas une URL Epitech, ignorer (sauf si c'est un lien relatif)
                if not url_clean.startswith('/') and not url_clean.startswith('./'):
                    continue
            
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

            # Campus internationaux - Détection améliorée
            if ".es" in url_lower or "epitech-it.es" in url_lower:
                pays = "Espagne"
                is_campus = True
                # Chercher Madrid ou Barcelone dans l'URL ou le texte du lien
                text_lower_link = text.lower() if text else ""
                
                if "madrid" in text_lower_link or "madrid" in url_lower:
                    ville = "Madrid"
                elif "barcelone" in text_lower_link or "barcelona" in text_lower_link or "barcelone" in url_lower or "barcelona" in url_lower:
                    ville = "Barcelone"
                else:
                    # Si le lien epitech-it.es n'a pas de ville spécifique dans le texte,
                    # on cherche dans le contexte de la page (parent, suivant, etc.)
                    # Pour l'instant, on crée Barcelone par défaut
                    # (Madrid sera détecté ailleurs si présent sur la page)
                    ville = "Barcelone"
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
                # Utiliser l'URL comme clé unique pour éviter les doublons
                if url_clean not in seen_urls and ville.lower() not in seen_cities:
                    seen_urls.add(url_clean)
                    seen_cities.add(ville.lower())
                    link_count += 1
                    print(f"   ✓ Campus détecté (lien {link_count}): {ville} ({pays}) -> {url_clean}")
                    # On suit le lien pour aller chercher les détails
                    yield response.follow(
                        url_clean, 
                        callback=self.parse_details, 
                        cb_kwargs={'ville': ville, 'pays': pays, 'url_base': url_clean},
                        dont_filter=True
                    )
        
        print(f"   📊 Total campus détectés depuis les liens: {link_count}")
        print(f"   📊 Total villes uniques détectées: {len(seen_cities)}")

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