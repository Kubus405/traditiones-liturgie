"""Office alternatives from the public dated ILG selector.

Publishes short descriptions and links ONLY (never the copyrighted text).
Do not infer that a local celebration applies nationwide.
"""
import datetime as dt
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests


def index_url(day: dt.date) -> str:
    return f'https://www.brewiarz.pl/x_{day.year % 100:02d}/{day.day:02d}{day.month:02d}/index.php3'


def office_color(title: str, day: dt.date) -> tuple[str, str]:
    """Only confident, simple rubrical indicators; defer uncertain cases to Ordo."""
    name = title.lower()
    if any(token in name for token in ('męczennic', 'męczennik', 'apostoł', 'ewangelist')):
        return 'czerwony', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if 'zesłanie ducha świętego' in name or 'niedziela palmowa' in name:
        return 'czerwony', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if any(token in name for token in ('poświęcenia bazyliki', 'poświęcenia kościoła',
                                       'jana pawła ii', 'papieża', 'najświętszej maryi')):
        return 'biały', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if any(token in name for token in ('zmartwychwstania', 'wielkanoc', 'boże narodzenie',
                                       'objawienie pańskie', 'wniebowstąpienie')):
        return 'biały', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if 'wielkiego postu' in name or 'adwentu' in name:
        return 'fioletowy', 'Orientacyjnie z okresu liturgicznego — potwierdź w Ordo.'
    if ('okresu zwykłego' in name or 'tygodnia zwykłego' in name):
        return 'zielony', 'Orientacyjnie z okresu liturgicznego — potwierdź w Ordo.'
    return 'nieustalony', 'Nie można jednoznacznie ustalić automatycznie; sprawdź Ordo.'


def _office_url(href: str, day: dt.date):
    url = urljoin(index_url(day), href)
    p = urlparse(url)
    # Never accept redirects / arbitrary URLs injected into downloaded HTML.
    if p.scheme != 'https' or p.hostname not in ('www.brewiarz.pl', 'brewiarz.pl'):
        return None
    desired = rf'^/x_{day.year % 100:02d}/{day.day:02d}{day.month:02d}(p|w[0-9]+)/index\.php3$'
    m = re.fullmatch(desired, p.path)
    if not m:
        return None
    return m.group(1), f'https://www.brewiarz.pl{p.path}'


def parse_offices(day: dt.date, html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if str(day.year) not in title and not re.search(r'wybierz oficjum', soup.get_text(' ', strip=True), re.I):
        raise ValueError('Brak pewnej daty lub wyboru oficjum na stronie.')

    result = []
    options = []
    for a in soup.find_all('a', href=True):
        parsed = _office_url(a['href'], day)
        if parsed is not None and a.get_text(' ', strip=True):
            options.append((a, *parsed))
    for number, (anchor, suffix, url) in enumerate(options):
        name = re.sub(r'\s+', ' ', anchor.get_text(' ', strip=True)).strip()
        if len(name) < 5 or len(name) > 190:
            continue
        # Context appears immediately before the office link, outside the <a>.
        # Stop scanning at previous option to avoid mixing local jurisdictions.
        pieces = []
        for node in anchor.previous_elements:
            if node is anchor or node is anchor.parent:
                continue
            if getattr(node, 'name', None) == 'a':
                other = node.attrs.get('href', '')
                if _office_url(other, day):
                    break
            if isinstance(node, str):
                val = re.sub(r'\s+', ' ', str(node)).strip()
                if val:
                    pieces.append(val)
            if len(' '.join(pieces)) > 650:
                break
        previous = ' '.join(reversed(pieces))
        scope = ''
        # Local jurisdiction is in preceding text, usually ending in ':'.
        matches = list(re.finditer(r'(?i)(?:\bW\s+(?:Wadowicach|powiatach|województwach|diecezji|bazylice|II Zakonie|mieście|archidiecezji)[^:]{0,380}:|\bPoza Polską:)', previous))
        if matches:
            scope = matches[-1].group(0).rstrip(': ').strip()
        elif 'poza polską:' in previous.lower():
            scope = 'Poza Polską'
        # Multiple options may link to same office page, but have distinct scope.
        if not scope and number > 0 and suffix == 'w1':
            scope = 'Obchód lokalny'
        color, note = office_color(name, day)
        result.append({
            'id': f'{suffix}-{len(result)}',
            'title': name, 'scope': scope, 'page_url': url,
            'reading_url': url.replace('/index.php3', '/czyt.php3'),
            'color': color, 'color_note': note,
            'source_code': suffix,
        })
    if not result:
        # Many weekdays do not have an office selector. The index redirects to
        # a single dated office; don't break daily publishing on ordinary days.
        color, note = 'nieustalony', 'Kolor zostanie określony z formularza dnia.'
        url = index_url(day).replace('/index.php3', 'p/index.php3')
        result = [{
            'id': 'p-0', 'title': 'Obchód dnia', 'scope': '',
            'page_url': url, 'reading_url': url.replace('/index.php3', '/czyt.php3'),
            'color': color, 'color_note': note, 'source_code': 'p',
        }]
    return result


def fetch_offices(day: dt.date) -> list[dict]:
    r = requests.get(index_url(day), timeout=25, headers={
        'User-Agent': 'TraditionesPersonalLiturgicalAid/1.1 (office metadata only)'
    })
    r.raise_for_status()
    r.encoding = r.apparent_encoding or 'utf-8'
    return parse_offices(day, r.text)
