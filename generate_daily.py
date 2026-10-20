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
        r'\d{1,3}(?:\s*\(\d{1,3}\))?,?\s*\d+[a-z]?(?:\s*[-–.]\s*\d+[a-z]?)?',
        content[:370])
    return matches[0].strip() if matches else ''


def parse_source_html(day, html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    # This checks the specific calendar date, not merely the year.
    dates = (f'{day.day} ', f'{day.day:02d}.')
    if str(day.year) not in title or not any(x in title for x in dates):
        raise ValueError(f'Niepewna data strony źródłowej: {title[:100]!r}')
    for elt in soup(['script', 'style', 'nav', 'footer']):
        elt.decompose()
    lines = [re.sub(r'\s+', ' ', line).strip()
             for line in soup.get_text('\n', strip=True).splitlines()]
    lines = [s for s in lines if s]
    # "Kolor szat" describes the vestment colour, NOT the celebration.
    # Never use a colour or an unrelated line as the liturgical day name.
    color_positions = [i for i, x in enumerate(lines)
                       if x.lower().startswith('kolor szat:')]
    if not color_positions:
        raise ValueError('Nie znaleziono opisu koloru szat liturgicznych')
    idx = color_positions[-1]
    color_line = lines[idx].split(':', 1)[1].strip()
    colour_only = re.fullmatch(
        r'(?:biały|biała|zielony|zielona|czerwony|czerwona|fioletowy|fioletowa|'
        r'różowy|różowa|czarny|czarna)(?:\s*(?:/|lub|albo|,|i)\s*'
        r'(?:biały|biała|zielony|zielona|czerwony|czerwona|fioletowy|fioletowa|'
        r'różowy|różowa|czarny|czarna))*\.?',
        color_line, flags=re.I)
    if colour_only:
        # The source may place the celebration on a neighbouring line.
        # Accept it only if it clearly looks like a liturgical celebration.
        neighbours = lines[max(0, idx - 3):idx] + lines[idx + 1:idx + 4]
        patterns = (r'\b(?:wspomnienie|święto|uroczystość|niedziela|dzień powszedni|'
                    r'feria|oktawa|sobota|poniedziałek|wtorek|środa|czwartek|piątek)\b')
        candidates = [x for x in neighbours if re.search(patterns, x, re.I)
                      and not x.lower().startswith('kolor szat:')
                      and 8 <= len(x) <= 180]
        if len(candidates) != 1:
            raise ValueError('Nie udało się jednoznacznie odczytać nazwy obchodu; '
                             f'kolor szat: {color_line!r}, kandydaci: {candidates!r}')
        raw_celebration = candidates[0]
    else:
        # Some page versions combine colour and celebration on one line.
        raw_celebration = re.sub(
            r'^(?:biały|biała|zielony|zielona|czerwony|czerwona|'
            r'fioletowy|fioletowa|różowy|różowa|czarny|czarna)\b[\s,;:–-]*',
            '', color_line, flags=re.I).strip()
    raw_celebration = re.sub(
        r'^(?:Poniedziałek|Wtorek|Środa|Czwartek|Piątek|Sobota|Niedziela),?\s*'
        r'\d{1,2}\s+[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+\s+\d{4}\s*',
        '', raw_celebration, flags=re.I).strip()
if not raw_celebration or len(raw_celebration) > 180:
    raise ValueError(
        f'Niepewna nazwa obchodu liturgicznego; '
        f'kolor={color_line!r}; '
        f'odczyt={raw_celebration!r}; '
        f'okolica={lines[max(0, idx-5):idx+6]!r}'
    )    sections = {}
    for k, v in SLOT_TITLES.items():
        if k == 'second_reading' and not _indices(lines, v):
            continue
        sections[k] = _section(lines, v)
    ref = {k: _ref(val, SLOT_TITLES[k]) for k, val in sections.items()}
    # Do not publish guessed Bible citations: those sections must be on source page.
    if not ref['readings'] or not ref['psalm'] or not ref['gospel']:
        raise ValueError(f'Brak jednoznacznych siglów: {ref!r}')
    antiphon = sections['antiphon'].removeprefix(SLOT_TITLES['antiphon'])
    primary = next((theme for theme, needles in MOTIFS
                    if any(needle in antiphon.lower() for needle in needles)), 'wiara')
    saint_match = re.search(r'\b(?:ŚW\.|ŚWIĘTEGO|ŚWIĘTEJ)\s+(.+?)(?:,|\bWspomnienie\b|\bUroczystość\b|$)',
                            raw_celebration, flags=re.I)
    saint = (('Św. ' + saint_match.group(1).strip().title()) if saint_match
             else 'Brak odrębnego wspomnienia świętego w wybranym formularzu')
    return {'celebration': raw_celebration, 'saint_name': saint,
            'sections': sections, 'ref': ref, 'theme': primary}


def fetch_source(day):
    url = source_url(day)
    response = requests.get(url, timeout=35, headers={
        'User-Agent': 'TraditionesPersonalLiturgicalAid/1.0 (source references only)'})
    response.raise_for_status()
    response.encoding = response.apparent_encoding or 'utf-8'
    return url, parse_source_html(day, response.text)


def compose(day, url, src):
    theme = src['theme']
    motif = DESCRIPTIONS[theme]
    refs = src['ref']
    celebration = src['celebration']
    saint = src['saint_name']
    is_saint = saint.startswith('Św.')
    intro = (
        f'Gromadzimy się na Eucharystii w dniu, w którym Kościół obchodzi: {celebration}. '
        f'Antyfona na wejście kieruje naszą uwagę na {motif}. '
        'Pragniemy otworzyć serca na Boże słowo i z wiarą uczestniczyć w świętych misteriach. '
        f'Usłyszymy czytanie oznaczone siglami {refs["readings"]}, a następnie Ewangelię {refs["gospel"]}. '
        'Prośmy Boga, aby usłyszane słowo przyniosło owoce w naszej modlitwie, '
        'w rodzinach i w codziennych spotkaniach z ludźmi.'
    )
    saint_description = (
        f'W kalendarzu liturgicznym na ten dzień wskazano obchód: {celebration}. '
        'Życiorys i patronat świętego należy sprawdzić w wiarygodnym źródle hagiograficznym; '
        'ten automatyczny opis nie dodaje niezweryfikowanych szczegółów.'
        if is_saint else
        f'Dzisiejszy formularz określono jako: {celebration}. '
        'Nie przypisujemy temu dniowi patrona, którego nie wymieniono w odczytanym formularzu.'
    )
    intercessions = {
        'introduction': f'Z wiarą zanieśmy nasze prośby do Boga, którego słowo prowadzi nas ku temu, co dobre. Pamiętając o {motif}, módlmy się wspólnie:',
        'petitions': [
            'Módlmy się za Kościół i jego pasterzy, aby wiernie głosili Ewangelię i prowadzili ludzi do Chrystusa. Ciebie prosimy.',
            'Módlmy się za rządzących narodami, aby troszczyli się o sprawiedliwość, pokój i godność każdego człowieka. Ciebie prosimy.',
            'Módlmy się za ubogich, chorych i osamotnionych, aby spotkali życzliwą pomoc i nie tracili nadziei. Ciebie prosimy.',
            'Módlmy się za rodziny i młodych, aby w codzienności kierowali się miłością i szacunkiem. Ciebie prosimy.',
            'Módlmy się za nas zgromadzonych na Eucharystii, abyśmy umieli wprowadzać usłyszane słowo w czyn. Ciebie prosimy.',
        ],
        'conclusion': 'Boże, nasz Ojcze, przyjmij modlitwy swojego ludu i ucz nas wypełniać Twoją wolę. Przez Chrystusa, Pana naszego. Amen.',
    }
    themes = [THEMES_FOR_SONGS.get(theme, theme), 'eucharystia', 'dziękczynienie']
    prefaces, preface_note = choose_prefaces(day, celebration)
    chants = make_chants(day, refs)
    return {
        'date': day.isoformat(), 'rite': 'Novus Ordo — kalendarz ogólnopolski',
        'source_url': url,
        'generated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'celebration': celebration,
        'liturgical_color': 'Sprawdź w źródle',
        'antiphon_summary': f'Antyfona na wejście zwraca uwagę na {motif}. Pełny tekst: pod podanym źródłem.',
        'introduction': intro, 'saint_name': saint, 'saint_description': saint_description,
        'readings_reference': refs['readings'],
        'readings_summary': 'Pierwsze czytanie wskazane w formularzu dnia. Przeczytaj jego pełny tekst w źródle przed liturgią.',
        'second_reading_reference': refs.get('second_reading', ''),
        'second_reading_summary': 'Drugie czytanie, gdy występuje; pełny tekst pod odnośnikiem źródłowym.' if refs.get('second_reading') else '',
        'psalm_reference': refs['psalm'],
        'psalm_summary': 'Psalm responsoryjny jest odpowiedzią wspólnoty na usłyszane słowo Boże. Refren i zwrotki znajdują się pod odnośnikiem.',
        'acclamation_reference': refs['acclamation'] or 'Sprawdź w źródle',
        'acclamation_summary': 'Śpiew przed Ewangelią przygotowuje nas do słuchania słów Chrystusa. Tekst i ewentualną zmianę aklamacji sprawdź w źródle.',
        'gospel_reference': refs['gospel'],
        'gospel_summary': 'Dzisiejsza Ewangelia zaprasza do słuchania Chrystusa i odpowiadania na Jego wezwanie swoim życiem.',
        'intercessions': intercessions,
        'songs': choose_songs(themes, day),
        'prefaces': prefaces,
        'prefaces_note': preface_note,
        'chant': chants,
        'note': 'Automatyczna propozycja z szablonu, nie oficjalny komentarz do czytań. Weryfikuj przed liturgią.',
    }


def produce(day, *, replace=False):
    out = OUTDIR / f'{day.isoformat()}.json'
    if out.exists() and not replace:
        print(f'Pomijam gotowy dzień: {out.name}')
        return
    url, src = fetch_source(day)
    data = compose(day, url, src)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(out)
    print(f'Wygenerowano: {out.name} — {data["celebration"]}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=4)
    parser.add_argument('--date', type=dt.date.fromisoformat)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.days <= 7:
        parser.error('Parametr --days musi należeć do zakresu 1–7')
    start = args.date or dt.datetime.now(ZoneInfo('Europe/Warsaw')).date()
    today_failed = False
    for i in range(args.days):
        day = start + dt.timedelta(days=i)
        try:
            produce(day, replace=args.replace)
        except Exception as exc:
            print(f'UWAGA — brak wpisu na {day.isoformat()}: {exc}', file=sys.stderr)
            if i == 0:
                today_failed = True
    if today_failed:
        raise SystemExit('Nie udało się przygotować aktualnego dnia — nie publikuj starszych danych jako dzisiejsze')


if __name__ == '__main__':
    main()
