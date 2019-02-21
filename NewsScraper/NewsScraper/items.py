# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, MapCompose, Join, TakeFirst
from datetime import date
import re
clean_text = Compose(MapCompose(lambda v: v.strip()), Join())
to_int = Compose(TakeFirst(), int)
to_date = Compose(TakeFirst(), date)
class NewsItem(scrapy.Item):
    titulo = scrapy.Field()
    texto = scrapy.Field()
    url = scrapy.Field()
    fecha = scrapy.Field()
    strategy = scrapy.Field()


class NewsItemLoader(ItemLoader):
    default_item_class = NewsItem
    titulo_out = clean_text
    texto_out = clean_text
    fecha_out = to_date



def obtenerFecha(response):
    regex_fechas = r"(lun(es)?|mar(tes)?|(miércoles|mie|mié|miercoles)|jue(ves)?|vie(rnes)?|s([áa])b(ado)?|dom(ingo)?)" \
                   r"(\s*,?)\s+([0-9]{2})\s+de\s+" \
                   r"(ene(ro)?|feb(rero)?|mar(zo)?|abr(il)?|may(o)?|jun(io)?|jul(io)?|ago(sto)?|sep(tiembre)?|oct(ubre)?|nov(iembre)?|dic(iembre)?)\s+" \
                   r"(del)?\s+([0-9]{4})"
    re1 = re.compile(regex_fechas, re.I)
    regex_fecha_simple = r"[0-9]{2}\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+[0-9]{4}"
    re2 = re.compile(regex_fecha_simple, re.I)
    ddmmyyyy = "[0-9]{2}/[0-9]{2}/[0-9]{4}"
    yyyymmdd = "[0-9]{4}/[0-9]{2}/[0-9]{2}"

    strategy = 1
    text_nodes = response.css("div,p,span").xpath("//text()")
    fecha = None
    # Estrategia 2 Matching all text nodes and filtering which ones look like a date
    if fecha is None:
        fecha = text_nodes.re_first(ddmmyyyy)
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
        fecha = response.xpath("//time/@datetime").get()
        strategy = 0
    return (fecha, strategy)