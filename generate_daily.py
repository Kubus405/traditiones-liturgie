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
    # The page's "Kolor szat" label is NOT the name of the celebration.
    # On the live site the date and celebration can be in the SAME element
    # or split among several HTML tags. Look only in the day-header region,
    # demand the EXACT local date, then read what follows that date.
    positions = [i for i, line in enumerate(lines)
                 if line.lower().startswith('kolor szat:')]
    if len(positions) != 1:
        raise ValueError(f'Nie znaleziono jednoznacznego nagłówka dnia: {len(positions)}')
    pos = positions[0]
    header = []
    for line in lines[pos:pos + 12]:
        if line.lower().startswith(('teksty liturgii mszy',
                                    'inne dostępne formularze',
                                    'antyfona na wejście')):
            break
        header.append(line)
    header_text = ' '.join(header)
    polish_months = ('', 'stycznia', 'lutego', 'marca', 'kwietnia', 'maja',
                     'czerwca', 'lipca', 'sierpnia', 'września',
                     'października', 'listopada', 'grudnia')
    date_match = re.search(
        rf'\b{day.day}\s+{polish_months[day.month]}\s+{day.year}\b',
        header_text, flags=re.I)
    if not date_match:
        raise ValueError(f'Brak zgodnej daty w nagłówku: {header_text[:230]!r}')
    raw_celebration = header_text[date_match.end():]
    # Icon captions and local optional formularies are not part of the day name.
    raw_celebration = re.split(
        r'\b(?:Kolor szat liturgicznych|W archidiecezji|W diecezji|'
        r'Teksty liturgii Mszy|Inne dostępne formularze)\b',
        raw_celebration, maxsplit=1, flags=re.I)[0].strip(' \u00a0;,:-')
    # Do not mistake a vestment colour or an image caption for a feast.
    if (not raw_celebration or len(raw_celebration) > 180 or
            re.fullmatch(r'(?:biały|zielony|czerwony|fioletowy|różowy|czarny)',
                         raw_celebration, flags=re.I)):
        raise ValueError('Niepewna nazwa obchodu liturgicznego; '
                         f'nagłówek: {header_text[:230]!r}; '
                         f'wynik: {raw_celebration!r}')
    sections = {}
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



# Autorskie wprowadzenia zweryfikowane dla konkretnego zestawu czytań.
# Nie stosować ich po zmianie formularza lub siglów lekcjonarza.
EDITORIAL_DAYS = {
    '2026-10-20': {
        'readings': 'Ef 2, 12-22', 'gospel': 'Łk 12, 35-38',
        'saint_name': 'Święty Jan Kanty',
        'saint_description': (
            'Święty Jan Kanty był kapłanem i profesorem Akademii Krakowskiej. '
            'Łączył pracę naukową z modlitwą i szczególną troską o ubogich. '
            'Jest patronem nauczycieli, uczniów i studentów.'
        ),
        'introduction': (
            'Drodzy Bracia i Siostry!\n\n'
            'W dzisiejszej liturgii wspominamy świętego Jana Kantego, kapłana i nauczyciela, '
            'który łączył umiłowanie prawdy z miłosierdziem wobec potrzebujących. '
            'Święty Paweł przypomina nam, że przez Chrystusa nie jesteśmy już obcymi, '
            'lecz domownikami Boga. W Ewangelii Pan Jezus wzywa nas do czuwania '
            'i gotowości na Jego przyjście.\n\n'
            'Prośmy, aby ta Eucharystia umocniła naszą wiarę, nauczyła dostrzegać '
            'Chrystusa w drugim człowieku i pomogła nam wiernie odpowiadać '
            'na Boże wezwanie każdego dnia.'
        ),
        'intercessions': {
            'introduction': (
                'Bracia i Siostry, za przykładem świętego Jana Kantego, '
                'który służył Bogu i ludziom, z ufnością przedstawmy nasze prośby:'
            ),
            'petitions': [
                'Módlmy się za Kościół, aby głosząc Chrystusa, prowadził ludzi ku jedności i pokojowi. Ciebie prosimy.',
                'Módlmy się za nauczycieli, wychowawców i studentów, aby poszukiwanie prawdy łączyli z szacunkiem i troską o bliźnich. Ciebie prosimy.',
                'Módlmy się za ubogich, chorych i osamotnionych, aby nie zabrakło im pomocy i ludzkiej życzliwości. Ciebie prosimy.',
                'Módlmy się za nas samych, abyśmy byli gotowi na spotkanie z Panem i wiernie pełnili Jego wolę. Ciebie prosimy.',
                'Módlmy się za naszych zmarłych, aby Bóg przyjął ich do radości życia wiecznego. Ciebie prosimy.',
            ],
            'conclusion': (
                'Boże, źródło pokoju i miłosierdzia, wysłuchaj naszych modlitw '
                'i naucz nas służyć Tobie w naszych bliźnich. Przez Chrystusa, Pana naszego. Amen.'
            ),
        },
    },
    '2026-10-21': {
        'readings': 'Ef 3, 2-12', 'gospel': 'Łk 12, 39-48',
        'introduction': (
            'Drodzy Bracia i Siostry!\n\n'
            'Przychodzimy dziś do ołtarza, aby zaczerpnąć siły z Bożego słowa '
            'i z Eucharystii. Święty Paweł przypomina, że obietnica zbawienia '
            'została otwarta dla wszystkich narodów, a w Chrystusie możemy '
            'z ufnością zbliżać się do Ojca. W Ewangelii Jezus wzywa uczniów '
            'do czujności i odpowiedzialności za to, co zostało im powierzone.\n\n'
            'Prośmy Pana o serca gotowe do służby, abyśmy nie odkładali dobra na później '
            'i potrafili wiernie wypełniać nasze codzienne obowiązki.'
        ),
        'intercessions': {
            'introduction': (
                'Zebrani przy stole słowa Bożego i Eucharystii, prośmy Ojca, '
                'aby uczynił nas wiernymi świadkami swojej miłości:'
            ),
            'petitions': [
                'Módlmy się za Kościół, aby wszystkim narodom głosił Ewangelię zbawienia. Ciebie prosimy.',
                'Módlmy się za rządzących, aby powierzoną im władzę wykorzystywali dla dobra wspólnego. Ciebie prosimy.',
                'Módlmy się za ludzi samotnych i zniechęconych, aby znaleźli wspólnotę i nadzieję. Ciebie prosimy.',
                'Módlmy się za nasze rodziny, aby nie brakowało w nich cierpliwości, odpowiedzialności i przebaczenia. Ciebie prosimy.',
                'Módlmy się za zmarłych, aby zostali dopuszczeni do udziału w uczcie niebieskiej. Ciebie prosimy.',
            ],
            'conclusion': (
                'Boże, nasz Ojcze, przyjmij prośby swojego ludu i umacniaj nas '
                'w wiernym pełnieniu Twojej woli. Przez Chrystusa, Pana naszego. Amen.'
            ),
        },
    },
}

# Dni nieobjęte redakcją otrzymują godne, ale OGÓLNE wprowadzenie.
# Nie wolno udawać, że automatyczny szablon komentuje dane czytania.
PASTORAL_OPENINGS = (
    'Drodzy Bracia i Siostry!\n\nStajemy dziś przed Bogiem, aby wsłuchać się w Jego słowo i przyjąć dar Eucharystii.',
    'Bracia i Siostry!\n\nPrzychodzimy na tę Mszę Świętą z naszymi radościami, troskami i nadzieją, że Pan jest pośród nas.',
    'Drodzy Bracia i Siostry!\n\nWspólna modlitwa gromadzi nas przy ołtarzu Chrystusa, który nieustannie obdarza swój Kościół łaską.',
    'Bracia i Siostry!\n\nRozpoczynając Eucharystię, powierzmy Panu wszystko, co przeżywamy, i otwórzmy serca na Jego obecność.',
)
PASTORAL_MOTIFS = {
    'miłosierdzie': 'Antyfona na wejście przypomina o miłosierdziu Boga. Niech Jego dobroć pobudza nas do przebaczenia i pomocy potrzebującym.',
    'miłość': 'Dzisiejsza antyfona kieruje nasze myśli ku miłości, która ma wyrażać się w naszych czynach i słowach.',
    'pokój': 'Antyfona na wejście przywołuje dar pokoju. Prośmy, by Pan uzdrawiał podziały i uczył nas pojednania.',
    'dziękczynienie': 'Dziękujmy dziś Bogu za otrzymane dobro i prośmy o wdzięczne serce także pośród codziennych trudności.',
    'wspólnota': 'Przypomnijmy sobie, że wiara prowadzi nas do wspólnoty: jesteśmy odpowiedzialni jedni za drugich.',
    'zaufanie': 'Powierzmy Panu to, co budzi nasz niepokój, i uczmy się z ufnością przyjmować Jego prowadzenie.',
    'opieka': 'Bóg nie pozostawia nas samych. Niech świadomość Jego opieki umacnia naszą wiarę i nadzieję.',
    'nawrócenie': 'Niech ta liturgia będzie dla nas okazją do szczerego rachunku sumienia i odnowienia serca.',
    'zmartwychwstanie': 'W Chrystusie zmartwychwstałym odnajdujemy nadzieję silniejszą niż lęk i cierpienie.',
    'eucharystia': 'W Eucharystii Chrystus daje nam siebie. Przyjmijmy ten dar z wdzięcznością i wiarą.',
    'świątynia': 'Bóg pragnie zamieszkać wśród swojego ludu. Otwórzmy Mu serca i uczmy się żyć w Jego obecności.',
    'radość': 'Prawdziwa radość ma swoje źródło w Bogu. Niech udział w liturgii odnowi w nas tę nadzieję.',
    'wiara': 'Prośmy dziś o wiarę, która nie ogranicza się do słów, lecz przemienia nasze codzienne wybory.',
}
PASTORAL_ENDINGS = (
    'Niech słowo, które usłyszymy, znajdzie miejsce w naszym życiu, a Komunia Święta umocni nas do wiernej służby Bogu i ludziom.',
    'Prośmy, aby udział w tej Eucharystii pomógł nam rozpoznać dobro, do którego Pan nas wzywa, i odważnie je podejmować.',
    'Otwórzmy serca na łaskę Boga, abyśmy wychodząc z kościoła, potrafili nieść innym Jego pokój i miłość.',
    'Niech spotkanie z Chrystusem umocni nas w codziennych obowiązkach i nauczy dostrzegać potrzeby bliźnich.',
)


def _pastoral_texts(day, src):
    refs = src['ref']
    entry = EDITORIAL_DAYS.get(day.isoformat())
    if (entry is not None and
            refs.get('readings') == entry['readings'] and
            refs.get('gospel') == entry['gospel']):
        return (entry['introduction'], entry['intercessions'],
                'Indywidualnie opracowane wprowadzenie na podstawie czytań dnia.',
                entry.get('saint_name'), entry.get('saint_description'))

    # Zróżnicowanie formuł bez twierdzenia, że komentujemy konkretną Ewangelię.
    n = day.toordinal()
    introduction = ' '.join((
        PASTORAL_OPENINGS[n % len(PASTORAL_OPENINGS)],
        PASTORAL_MOTIFS.get(src['theme'], PASTORAL_MOTIFS['wiara']),
        PASTORAL_ENDINGS[(n // 4) % len(PASTORAL_ENDINGS)],
    ))
    petitions = [
        'Módlmy się za Kościół i jego pasterzy, aby wiernie prowadzili ludzi do Chrystusa. Ciebie prosimy.',
        'Módlmy się za odpowiedzialnych za życie społeczne, aby kierowali się sprawiedliwością i troską o najsłabszych. Ciebie prosimy.',
        'Módlmy się za chorych, ubogich i samotnych, aby otrzymali potrzebną pomoc i wsparcie. Ciebie prosimy.',
        'Módlmy się za nas zgromadzonych przy ołtarzu, abyśmy przyjmowali słowo Boże i żyli nim każdego dnia. Ciebie prosimy.',
        'Módlmy się za zmarłych, aby Pan obdarzył ich pokojem wiecznym. Ciebie prosimy.',
    ]
    intercessions = {
        'introduction': 'Bracia i Siostry, ufając dobroci naszego Ojca, przedstawmy Mu prośby Kościoła i całego świata:',
        'petitions': petitions,
        'conclusion': ('Boże, nasz Ojcze, wysłuchaj modlitw swojego ludu '
                       'i umacniaj nas w miłości. Przez Chrystusa, Pana naszego. Amen.'),
    }
    return (introduction, intercessions,
            'Wprowadzenie ogólne oparte na motywie antyfony; nie jest komentarzem do konkretnych czytań.',
            None, None)


def compose(day, url, src):
    theme = src['theme']
    motif = DESCRIPTIONS[theme]
    refs = src['ref']
    celebration = src['celebration']
    saint = src['saint_name']
    is_saint = saint.startswith('Św.')
    intro, intercessions, editorial_note, saint_override, saint_desc_override = _pastoral_texts(day, src)
    if saint_override:
        saint = saint_override
    saint_description = saint_desc_override or (
        'Patrona lub świętego wspominanego w liturgii dnia można sprawdzić '
        'w kalendarzu liturgicznym pod podanym odnośnikiem.'
        if is_saint else
        'W formularzu dnia nie wskazano odrębnego wspomnienia patrona. '
        'Sprawdź kalendarz lokalny, ponieważ obchody diecezjalne mogą się różnić.'
    )
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
        'introduction_note': editorial_note,
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
        'note': editorial_note + ' Modlitwa wiernych jest propozycją autorską; przed użyciem wymaga zatwierdzenia przez celebransa.',
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
