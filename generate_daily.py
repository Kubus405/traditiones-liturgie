#!/usr/bin/env python3
"""Free, rule-based Polish daily liturgy aide.

Reads the public dated page to identify the day and references; publishes only
short original templated aids and approved song titles, never the full readings.
No paid API, generative AI, credentials, or payment method required.
Source layout may change: fail closed instead of inventing readings or dates.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from song_catalog import choose_songs
from prefaces import choose_prefaces
from chant_notation import make_chants

OUTDIR = Path(__file__).parent / 'site' / 'dni'
SLOT_TITLES = {
    'antiphon': 'ANTYFONA NA WEJŚCIE',
    'readings': 'PIERWSZE CZYTANIE',
    'second_reading': 'DRUGIE CZYTANIE',
    'psalm': 'PSALM RESPONSORYJNY',
    'acclamation': 'ŚPIEW PRZED EWANGELIĄ',
    'gospel': 'EWANGELIA',
}
MOTIFS = [
    ('miłosierdzie', ['miłosierd', 'lituje', 'przebacz', 'łaskaw']),
    ('miłość', ['miłości', 'miłość', 'miłuj', 'kochaj']),
    ('pokój', ['pokoju', 'pokój', 'pojednan']),
    ('dziękczynienie', ['dziękuj', 'dziękczyn', 'wdzięcz']),
    ('wspólnota', ['wspólnot', 'jednośc', 'jedność', 'bracia', 'braci']),
    ('zaufanie', ['zaufa', 'nadziej', 'ufnośc', 'ufność']),
    ('opieka', ['opieka', 'opiekę', 'schronien', 'ochron']),
    ('nawrócenie', ['nawróc', 'pokuta', 'pokutę']),
    ('zmartwychwstanie', ['zmartwychwst', 'powstał z martwych']),
    ('eucharystia', ['eucharyst', 'chleb żyw', 'ciało moje']),
    ('świątynia', ['świąty', 'przybytek', 'przybytki']),
    ('radość', ['radośc', 'radość', 'raduj']),
    ('wiara', ['wiar', 'wierzy', 'wiernych']),
]
DESCRIPTIONS = {
    'miłosierdzie': 'miłosierdzie Boga i nasze powołanie do okazywania dobra bliźnim',
    'miłość': 'miłość Boga, która ma stawać się czynem w codziennym życiu',
    'pokój': 'pokój i pojednanie, do których zaprasza nas Pan',
    'dziękczynienie': 'wdzięczność wobec Boga za otrzymane dary',
    'wspólnota': 'jedność Ludu Bożego i troskę o innych',
    'zaufanie': 'zaufanie Bożej obecności również pośród trudności',
    'opieka': 'Bożą opiekę nad człowiekiem',
    'nawrócenie': 'wezwanie do przemiany serca',
    'zmartwychwstanie': 'nadzieję płynącą ze zmartwychwstania Chrystusa',
    'eucharystia': 'dar spotkania z Chrystusem w Eucharystii',
    'świątynia': 'świętość Bożej obecności pośród swojego ludu',
    'radość': 'radość płynącą z bliskości Pana',
    'wiara': 'wiarę, którą pragniemy wyznawać i przeżywać',
}
THEMES_FOR_SONGS = {'radość': 'uwielbienie'}


def source_url(day):
    return f'https://brewiarz.pl/x_{day.year % 100:02d}/{day.day:02d}{day.month:02d}p/czyt.php3'


def _indices(lines, title):
    return [i for i, line in enumerate(lines) if line.upper() == title or line.upper().startswith(title + ' ')]


def _section(lines, title):
    indices = _indices(lines, title)
    if not indices:
        raise ValueError(f'Nie znaleziono sekcji: {title}')
    i = indices[-1]
    cutoff = len(lines)
    for j in range(i + 1, min(i + 45, len(lines))):
        t = lines[j].upper()
        if t.startswith(('KOMENTARZ DO', 'WPROWADZENIE DO', 'KOLEKTA',
                         'MODLITWA NAD DARAMI', 'ANTYFONA NA KOMUNIĘ',
                         'REFLEKSJA NAD CZYTANIAMI')) or any(
                         t == heading or t.startswith(heading + ' ')
                         for heading in SLOT_TITLES.values()):
            cutoff = j
            break
    return ' '.join(lines[i:cutoff]).strip()


def _ref(section, title):
    content = section.removeprefix(title).strip()
    # A heading often includes its thematic subtitle, followed by the Bible citation.
    matches = re.findall(
        r'(?<!\w)(?:Por\.\s*)?(?:[1-3]\s*)?'
        r'(?:[A-ZŁŚŻŹĆŃ][a-ząćęłńóśźż]{1,8}|Ps)\s+'
