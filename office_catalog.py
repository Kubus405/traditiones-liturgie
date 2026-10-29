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
                                       'jana pawła ii', 'papieża', 'najświętszej maryi',
                                       'prezbitera', 'kapłana', 'wyznawcy')):
        return 'biały', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if any(token in name for token in ('zmartwychwstania', 'wielkanoc', 'boże narodzenie',
                                       'objawienie pańskie', 'wniebowstąpienie')):
        return 'biały', 'Orientacyjnie z rodzaju obchodu — potwierdź w Ordo.'
    if 'wielkiego postu' in name or 'adwentu' in name:
        return 'fioletowy', 'Orientacyjnie z okresu liturgicznego — potwierdź w Ordo.'
    if ('okresu zwykłego' in name or 'tygodnia zwykłego' in name):
        return 'zielony', 'Orientacyjnie z okresu liturgicznego — potwierdź w Ordo.'
    return 'nieustalony', 'Nie można jednoznacznie ustalić automatycznie; sprawdź Ordo.'


def _office_url(href: str, day: dt.date, base_url: str | None = None):
    url = urljoin(base_url or index_url(day), href)
    p = urlparse(url)
    # Never accept redirects / arbitrary URLs injected into downloaded HTML.
    if p.scheme != 'https' or p.hostname not in ('www.brewiarz.pl', 'brewiarz.pl'):
        return None
    # Some feasts use /ddmmp/ or /ddmmw/, while an ordinary weekday uses
    # /ddmm/ without any suffix. Local 'w' is also valid without a number.
    desired = rf'^/x_{day.year % 100:02d}/{day.day:02d}{day.month:02d}(p|w[0-9]*)?/index\.php3$'
    m = re.fullmatch(desired, p.path)
    if not m:
        return None
    return m.group(1) or '', f'https://www.brewiarz.pl{p.path}'


def source_readings_url(day: dt.date) -> str:
    """Fallback for a weekday without a selectable office (no 'p')."""
    return index_url(day).replace('/index.php3', '/czyt.php3')


def parse_offices(day: dt.date, html: str, *, base_url: str | None = None) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if str(day.year) not in title and not re.search(r'wybierz oficjum', soup.get_text(' ', strip=True), re.I):
        raise ValueError('Brak pewnej daty lub wyboru oficjum na stronie.')

    result = []
    options = []
    has_selector = bool(re.search(r'wybierz\s+oficjum', soup.get_text(' ', strip=True), re.I))
    for a in soup.find_all('a', href=True):
        parsed = _office_url(a['href'], day, base_url)
        if parsed is not None and a.get_text(' ', strip=True):
            # On a weekday the bare /ddmm/index.php3 link is normally a
            # breadcrumb, not a selectable office.
            if parsed[0] == '' and not has_selector:
                continue
            options.append((a, *parsed))
    for number, (anchor, suffix, url) in enumerate(options):
        name = re.sub(r'\s+', ' ', anchor.get_text(' ', strip=True)).strip()
        # ILG places a navigation link such as '29.10.2026 - Wybór oficjum'
        # before the actual celebrations. It is NOT a liturgical formulary.
        # This link used to become a fake, unverified office in the app.
        if re.search(r'wyb[oó]r\s+oficjum', name, re.I):
            continue
        # Do not turn a date breadcrumb pointing to the same page into a
        # selectable office.
        if (len(name) < 5 or len(name) > 190 or
                not re.search(r'[a-ząćęłńóśźż]{3,}', name, re.I)):
            continue
        # Context appears immediately before the office link, outside the <a>.
        # Stop scanning at previous option to avoid mixing local jurisdictions.
        pieces = []
        for node in anchor.previous_elements:
            if node is anchor or node is anchor.parent:
                continue
            if getattr(node, 'name', None) == 'a':
                other = node.attrs.get('href', '')
                if _office_url(other, day, base_url):
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
        # Ordinary weekdays typically use /ddmm/czyt.php3, WITHOUT 'p'.
        # Resolve the actual dated reading link from the source index instead
        # of inventing a /ddmmp/ URL that may not exist.
        color, note = 'nieustalony', 'Kolor zostanie określony z formularza dnia.'
        suffix = ''
        reading_url = source_readings_url(day)
        for a in soup.find_all('a', href=True):
            label = a.get_text(' ', strip=True).lower()
            if 'czytania liturgii mszy' not in label and 'czytania liturgiczne' not in label:
                continue
            candidate = urljoin(base_url or index_url(day), a['href'])
            parsed = urlparse(candidate)
            if (parsed.scheme != 'https' or
                    parsed.hostname not in ('www.brewiarz.pl', 'brewiarz.pl')):
                continue
            pattern = rf'^/x_{day.year % 100:02d}/{day.day:02d}{day.month:02d}(p|w[0-9]*)?/czyt\.php3$'
            m = re.fullmatch(pattern, parsed.path)
            if m:
                suffix = m.group(1) or ''
                reading_url = f'https://www.brewiarz.pl{parsed.path}'
                break
        # The default office can also be named on the index page.
        text_nodes = [re.sub(r'\s+', ' ', x).strip()
                      for x in soup.get_text('\n', strip=True).splitlines()]
        day_name = next((x for x in text_nodes if
            re.search(r'(?i)(?:poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela)\s+[IVXLCDM]+\s+tygodnia\s+okresu zwykłego', x)
            and len(x) < 120), 'Obchód dnia')
        color, note = office_color(day_name, day)
        result = [{
            'id': f'{suffix or "zwykly"}-0', 'title': day_name, 'scope': '',
            'page_url': base_url or index_url(day), 'reading_url': reading_url,
            'color': color, 'color_note': note, 'source_code': suffix,
        }]
    return result


def fetch_offices(day: dt.date) -> list[dict]:
    r = requests.get(index_url(day), timeout=25, headers={
        'User-Agent': 'TraditionesPersonalLiturgicalAid/1.1 (office metadata only)'
    })
    r.raise_for_status()
    r.encoding = r.apparent_encoding or 'utf-8'
    return parse_offices(day, r.text, base_url=r.url)
