"""Conservative selection of Polish Missal prefaces (number and name only).

Not an official ordo. A solemnity, local proper, parish titular day, a ritual
Mass, and optional formularies can override these suggestions. Return [] when
conditions cannot be classified reliably. Sources are linked in each group.
"""
import datetime as dt
import re
import unicodedata

BASE = 'https://biblia.kerygma.pl/eucharystia/prefacje/'
SOURCES = {
    'advent': BASE + '395-prefacje-okresu-adwentu-nr-1-2-i-narodzenia-panskiego-nr-3-7',
    'lent': BASE + '396-prefacje-okresu-wielkiego-postu-nr-8-19',
    'easter': BASE + '397-prefacje-okresu-wielkanocnego',
    'ordinary': BASE + '398-prefacje-okresu-zwyklego-28-41',
    'saints': BASE + '401-prefacje-o-aniolach-i-swietych-63-77',
}

PREFACES = {}

def _add(begin, names, *, category, description=''):
    for offset, name in enumerate(names):
        nr = begin + offset
        PREFACES[nr] = {
            'number': nr,
            'name': name,
            'source_url': SOURCES[category],
        }

_add(1, ['I prefacja adwentowa — Dwa przyjścia Chrystusa',
         'II prefacja adwentowa — Dwa oczekiwania na przyjście Chrystusa'], category='advent')
_add(3, ['I prefacja o Narodzeniu Pańskim — Chrystus Światłością',
         'II prefacja o Narodzeniu Pańskim — Wcielenie odnawia wszechświat',
         'III prefacja o Narodzeniu Pańskim — Wymiana między Bogiem a ludźmi w Słowie Wcielonym'], category='advent')
_add(8, ['I prefacja wielkopostna — Duchowe znaczenie Wielkiego Postu',
         'II prefacja wielkopostna — Odnowienie przez pokutę',
         'III prefacja wielkopostna — Motywy wstrzemięźliwości',
         'IV prefacja wielkopostna — Owoce postu'], category='lent')
_add(12, ['Prefacja na I niedzielę Wielkiego Postu — Kuszenie Chrystusa',
          'Prefacja na II niedzielę Wielkiego Postu — Przemienienie Pańskie',
          'Prefacja na III niedzielę Wielkiego Postu — Wiara Samarytanki',
          'Prefacja na IV niedzielę Wielkiego Postu — Oświecenie ludzi przez Chrystusa',
          'Prefacja na V niedzielę Wielkiego Postu — Wskrzeszenie Łazarza',
          'I prefacja o Męce Pańskiej — Potęga Krzyża',
          'II prefacja o Męce Pańskiej — Zwycięstwo męki',
          'Prefacja na Niedzielę Palmową — Śmierć Chrystusa zgładziła nasze winy'], category='lent')
_add(20, ['I prefacja wielkanocna — Misterium paschalne',
          'II prefacja wielkanocna — Nowe życie w Chrystusie',
          'III prefacja wielkanocna — Chrystus żyje i wstawia się za nami',
          'IV prefacja wielkanocna — Odnowa wszechświata przez misterium paschalne',
          'V prefacja wielkanocna — Chrystus Kapłanem i Ofiarą',
          'I prefacja o Wniebowstąpieniu — Chrystus uprzedził nas w chwale',
          'II prefacja o Wniebowstąpieniu — Chrystus daje nam udział w swoim bóstwie',
          'Prefacja o Zesłaniu Ducha Świętego — Zesłanie Ducha Świętego dopełnieniem dzieła zbawienia'], category='easter')
_add(28, ['I prefacja na niedziele zwykłe — Misterium paschalne i lud Boży',
          'II prefacja na niedziele zwykłe — Misterium zbawienia',
          'III prefacja na niedziele zwykłe — Zbawienie ludzi przez Boga-Człowieka',
          'IV prefacja na niedziele zwykłe — Dzieje zbawienia',
          'V prefacja na niedziele zwykłe — Dzieło stworzenia',
          'VI prefacja na niedziele zwykłe — Zadatek wieczystej Paschy',
          'VII prefacja na niedziele zwykłe — Zbawienie przez posłuszeństwo Chrystusa',
          'VIII prefacja na niedziele zwykłe — Jedność Trójcy źródłem jedności Kościoła'], category='ordinary')
_add(36, ['I prefacja zwykła — Odnowa świata przez Chrystusa',
          'II prefacja zwykła — Zbawienie przez Chrystusa',
          'III prefacja zwykła — Bóg Stwórca i Odkupiciel człowieka',
          'IV prefacja zwykła', 'V prefacja zwykła', 'VI prefacja zwykła'], category='ordinary')
_add(70, ['I prefacja o świętych — Chwała świętych',
          'II prefacja o świętych — Rola świętych w Kościele',
          'Prefacja o świętych męczennikach',
          'Prefacja o świętych pasterzach — Obecność świętych pasterzy w Kościele',
          'Prefacja o świętych dziewicach i zakonnikach'], category='saints')
PREFACES[63] = {'number': 63, 'name': 'Prefacja o aniołach — Chwała Boża jaśnieje w aniołach', 'source_url': SOURCES['saints']}
PREFACES[64] = {'number': 64, 'name': 'Prefacja o św. Janie Chrzcicielu — Posłannictwo Poprzednika Chrystusa', 'source_url': SOURCES['saints']}
# Known and verified for the feast of Saints Simon and Jude.
PREFACES[68] = {
    'number': 68,
    'name': 'II prefacja o Apostołach — Apostołowie fundamentem Kościoła i świadkami Boga',
    'source_url': 'https://www.kerygma.pl/liturgiczne/uroczystosci-i-swieta/475-swieci-apostolowie-szymon-i-juda-tadeusz',
}



def _canon(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                   if unicodedata.category(c) != 'Mn')


def easter_date(y):
    """Gregorian Easter."""
    a = y % 19
    b = y // 100
    c = y % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return dt.date(y, month, day)


def season(day):
    e = easter_date(day.year)
    ash = e - dt.timedelta(days=46)
    pentecost = e + dt.timedelta(days=49)
    christmas = dt.date(day.year, 12, 25)
    days_back = (christmas.weekday() + 1) % 7 or 7
    fourth_advent = christmas - dt.timedelta(days=days_back)
    start_advent = fourth_advent - dt.timedelta(days=21)
    if day >= start_advent and day < christmas:
        return 'advent'
    jan6 = dt.date(day.year, 1, 6)
    baptism = jan6 + dt.timedelta(days=(6 - jan6.weekday()) % 7 or 7)
    if day >= christmas or day <= baptism:
        return 'christmas'
    if ash <= day < e:
        return 'lent'
    if e <= day <= pentecost:
        return 'easter'
    return 'ordinary'


def _entries(numbers):
    return [PREFACES[n].copy() for n in numbers if n in PREFACES]


def choose_prefaces(day, celebration):
    """Return a safe shortlist and a human-readable caveat.

    Only suggest choices for a clearly identifiable common formular; do not
    falsely declare all possible prefaces on feasts with their own proper.
    """
    name = _canon(celebration)
    period = season(day)
    is_sunday = day.weekday() == 6
    saint = bool(re.search(r'\b(sw\.?|swiety|swietej|swietego|blogoslawion)', name))
    proper = any(x in name for x in (
        'uroczystosc', 'swieto', 'wniebowziecia', 'niepokalanego poczecia',
        'objawienia panskiego', 'chrztu panskiego', 'najswietszej trojcy',
        'bozego ciala', 'przemienienia panskiego', 'wszystkich swietych',
        'krola wszechswiata', 'ofiarowania panskiego',
    ))
    # Apostolic feasts use an attested specific preface in the Polish Missal.
    if 'apostol' in name or 'apostoł' in name:
        return _entries([68]), ('II prefacja o Apostołach (nr 68); '
                'w przypadku szczególnego obchodu lokalnego sprawdź Mszał i Ordo.')
    if proper:
        return [], 'Uroczystość lub święto: sprawdź prefację własną w Mszale albo Ordo. Lista ogólna nie może jej zastąpić.'
    if period == 'advent':
        return (_entries([1] if day.day < 17 or day.month == 11 else [2]),
                'Prefacja okresowa; sprawdź, czy formularz nie ma własnej prefacji.')
    if period == 'christmas':
        return _entries([3, 4, 5]), 'Właściwe dla okresu Narodzenia Pańskiego; obchody specjalne mogą mieć prefację własną.'
    if period == 'lent':
        if 'palmow' in name:
            return _entries([19]), 'Prefacja Niedzieli Palmowej.'
        if is_sunday:
            sunday_no = (day - easter_date(day.year)).days // 7 + 7
            # Proper 3/4/5 Sundays can depend on selected readings (year A).
            return (_entries([11 + sunday_no]) if 1 <= sunday_no <= 2 else [],
                    'W Wielkim Poście dobór prefacji niedzielnej zależy od formularza i czytań; sprawdź Ordo.')
        return _entries([8, 9, 10, 11]), 'Prefacje wielkopostne; w niektóre dni obowiązuje prefacja własna.'
    if period == 'easter':
        if 'zeslani' in name and 'ducha' in name:
            return _entries([27]), 'Prefacja własna na Zesłanie Ducha Świętego.'
        if day == easter_date(day.year):
            return _entries([20]), 'W Niedzielę Zmartwychwstania szczególnie I prefacja wielkanocna.'
        return _entries([20, 21, 22, 23, 24]), 'Prefacje wielkanocne; święta i uroczystości mogą mieć własne.'
    if saint:
        choices = []
        if 'meczenn' in name:
            choices.append(72)
        if any(x in name for x in ['prezbiter', 'biskup', 'papiez', 'pasterz', 'kaplan']):
            choices.append(73)
        if any(x in name for x in ['dziewic', 'zakonn', 'opata', 'opatki']):
            choices.append(74)
        choices += [70, 71]
        if not is_sunday:
            choices += list(range(36, 42))
        return _entries(dict.fromkeys(choices)), ('Możliwe przy wspomnieniu świętego w okresie zwykłym; '
                'wybór zależy od formularza. Prefacja własna, jeśli przewidziana, ma pierwszeństwo.')
    if is_sunday:
        return _entries(range(28, 36)), 'Prefacje na niedziele zwykłe nr 28–35.'
    return _entries(range(36, 42)), 'Prefacje zwykłe nr 36–41.'
