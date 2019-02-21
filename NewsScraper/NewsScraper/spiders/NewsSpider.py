# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response
from urllib.parse import *
from ..items import *
import re



class NewsSpider(scrapy.Spider):
    name = 'NewsSpider'
    google_url = 'http://www.google.com/search?'
    stopwords = ["derechos", "reservados", "copyright", "©", "recibe nuestro newsletter", "registrate",
                 "accede por facebook"]
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
        yield scrapy.Request(self.google_url + urlencode(params), callback=self.parse)

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
        # Regex for dates
        regex_fechas = r"(lun(es)?|mar(tes)?|(miércoles|mie|mié|miercoles)|jue(ves)?|vie(rnes)?|s([áa])b(ado)?|dom(ingo)?)" \
                       r"(\s*,?)\s+([0-9]{2})\s+de\s+" \
                       r"(ene(ro)?|feb(rero)?|mar(zo)?|abr(il)?|may(o)?|jun(io)?|jul(io)?|ago(sto)?|sep(tiembre)?|oct(ubre)?|nov(iembre)?|dic(iembre)?)\s+" \
                       r"(del)?\s+([0-9]{4})"
        re1 = re.compile(regex_fechas, re.I)
        regex_fecha_simple = r"[0-9]{2}\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+[0-9]{4}"
        re2 = re.compile(regex_fecha_simple, re.I)
        ddmmyyyy = "[0-9]{2}/[0-9]{2}/[0-9]{4}"
        yyyymmdd = "[0-9]{4}/[0-9]{2}/[0-9]{2}"
        # Texto de la noticia
        texto_noticia = response.css("div > p").xpath("string()").getall()
        # Filter and remove whitespace from text. also remove paragraphs with stopwords or stop_phrases.
        texto_noticia = [p.strip() for p in texto_noticia if
                         len(p.strip()) > 20 and not any(stopword in p.lower() for stopword in self.stopwords)]
        # Strategy 1. time tag
        fecha = response.xpath("//time/@datetime").get()
        strategy = 1
        text_nodes = response.css("div,p,span").xpath("//text()")
        # Estrategia 2 Matching all text nodes and filtering which ones look like a date
        if fecha is None:
            fecha = text_nodes.re(ddmmyyyy)
            strategy = 2
        if fecha is None:
            fecha = text_nodes.re(yyyymmdd)
            strategy = 3
        if fecha is None:
            fecha = text_nodes.re(re1)
            strategy = 4
        if fecha is None:
            fecha = text_nodes.re(re2)
            strategy = 5
        if fecha is None:
            # Estrategia 3, buscar en los comentarios.
            fecha = response.xpath("//comment()").re("[0-9]{4}-[0-9]{2}-[0-9]{2}")
            strategy = 6
        if fecha is None:
            strategy = 0

        return {
            "title": response.meta["title"],
            "texto": texto_noticia,
            "url": response.url,
            "fecha": fecha,
            "strategy": strategy
        }
