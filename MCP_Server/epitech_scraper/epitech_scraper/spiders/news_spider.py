import scrapy

class EpitechNewsSpider(scrapy.Spider):
    name = "epitech_news"
    allowed_domains = ["epitech.eu"]
    start_urls = ["https://www.epitech.eu/fr/actualites-technologiques-informatiques/"]

    def parse(self, response):
        # On essaie de récupérer les titres des articles de news
        # Sélecteurs CSS adaptés à la structure probable du site (à ajuster si besoin)
        for article in response.css('article'):
            yield {
                'title': article.css('h2::text, h3::text').get(),
                'link': article.css('a::attr(href)').get(),
                'summary': article.css('p::text').get(),
            }

        # Pagination (optionnel, pour l'instant on reste simple)
        # next_page = response.css('a.next::attr(href)').get()
        # if next_page:
        #     yield response.follow(next_page, self.parse)
