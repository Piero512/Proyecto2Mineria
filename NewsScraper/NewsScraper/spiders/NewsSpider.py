# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response
from urllib.parse import *

class NewsSpider(scrapy.Spider):
    name = 'NewsSpider'
    google_url = 'http://www.google.com/search?'
    stopwords = ["derechos", "reservados", "copyright", "©", "recibe nuestro newsletter", "registrate", "accede por facebook"]
    # start_urls = [ google_url + urlencode(params)]
    tags = ["hambre", "economia", "represion"]
    google_next_selector = ".navend"
    # response.css(".g").xpath("string(.//a)").getall() is for getting titles in the result page.
    page_count = 0

    def start_requests(self):
        params = {
            "q": "%s" % (self.query if self.query is not None else "venezuela"),  # Query
            "safe": "active",  # Safesearch
            "tbm": "nws",  # News table
            "tbs": "cdr:1,cd_min:1/1/2018,cd_max:12/31/2018"  # From 1/1/2018 to 12/31/2018
        }
        yield scrapy.Request(self.google_url + urlencode(params), callback= self.parse)
    def parse(self, response):
        news_links = response.css(".g").xpath(".//a")
        # Filter news_link by length
        news_links = [selector for selector in news_links if len(selector.xpath("string(.)").get()) > 10]
        for newslink in news_links:
            newspage = response.urljoin(newslink.xpath("@href").get())
            yield scrapy.Request(newspage, callback=self.parse_news, meta={
                "title": newslink.xpath("string(.)").get()
            })
        next_page = response.css("td[class]:last-child a")  # Google makes it really hard to get to the next page.

        if next_page is not None and self.page_count < 30:
            # inspect_response(response,self)
            self.page_count += 1
            next_page_link = response.urljoin(next_page.xpath("@href").get())
            yield scrapy.Request(next_page_link, callback=self.parse)
        else:
            print(next_page)

    def parse_news(self, response):
        texto_noticia = response.css("div > p").xpath("string(.)").getall()
        # Filter and remove whitespace from text. also remove paragraphs with stopwords or stop_phrases.
        texto_noticia = [p.strip() for p in texto_noticia if len(p.strip()) > 20 and not any(stopword in p.lower() for stopword in self.stopwords )]
        return {
            "title": response.meta["title"],
            "texto": " ".join(texto_noticia),
            "url": response.url
        }
