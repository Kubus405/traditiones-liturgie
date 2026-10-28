"""Offline regression tests for dated ILG URLs. No network, no paid API."""
import datetime as dt
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from office_catalog import parse_offices
import generate_daily as generator

DAY_27 = dt.date(2026, 10, 27)
DAY_28 = dt.date(2026, 10, 28)

# 27 Oct 2026 was a normal weekday. ILG uses /2710/czyt.php3,
# not /2710p/czyt.php3. A breadcrumb MUST NOT be parsed as an office.
index_27 = '''<html><head><title>.:ILG:. - 27 października 2026</title></head>
<body><a href="/x_26/2710/index.php3">27 października 2026</a>
<p>Wtorek XXX tygodnia Okresu Zwykłego</p>
<a href="czyt.php3">Czytania liturgii Mszy św.</a></body></html>'''
ordinary = parse_offices(DAY_27, index_27)
assert len(ordinary) == 1, ordinary
assert ordinary[0]['source_code'] == '', ordinary
assert ordinary[0]['reading_url'] == 'https://www.brewiarz.pl/x_26/2710/czyt.php3'
assert ordinary[0]['title'] == 'Wtorek XXX tygodnia Okresu Zwykłego'
assert ordinary[0]['color'] == 'zielony'

# On some dates the index URL redirects to the p-suffixed office.
# A relative link must be resolved using the FINAL URL after redirect.
redirected = parse_offices(
    dt.date(2026, 10, 26),
    '''<html><title>26 października 2026</title><body>
    <p>Poniedziałek XXX tygodnia Okresu Zwykłego</p>
    <a href="czyt.php3">Czytania liturgii Mszy św.</a></body></html>''',
    base_url='https://www.brewiarz.pl/x_26/2610p/index.php3')
assert redirected[0]['source_code'] == 'p'
assert redirected[0]['reading_url'].endswith('/2610p/czyt.php3')

# 28 Oct 2026 feast includes a local office ending in /w/ (without number).
index_28 = '''<html><head><title>.:ILG:. - 28 października 2026</title></head>
<body><h1>WYBIERZ OFICJUM</h1>
<a href="/x_26/2810p/index.php3">Święto świętych Apostołów Szymona i Judy Tadeusza</a>
<p>W diecezji siedleckiej:
<a href="/x_26/2810w/index.php3">Uroczystość świętych Apostołów Szymona i Judy Tadeusza</a></p>
</body></html>'''
feast = parse_offices(DAY_28, index_28)
assert len(feast) == 2, feast
assert [i['source_code'] for i in feast] == ['p', 'w'], feast
assert feast[1]['reading_url'].endswith('/2810w/czyt.php3')

# A normal weekday must generate a valid dated JSON with unsuffixed URL.
src = {
    'theme': 'wiara', 'saint_name': 'Brak odrębnego wspomnienia',
    'celebration': 'XXX tydzień Okresu Zwykłego',
    'ref': {'readings': 'Ef 5, 21-33', 'psalm': 'Ps 128, 1-2',
            'second_reading': '', 'acclamation': 'Mt 11, 25',
            'gospel': 'Łk 13, 18-21'},
    'sections': {'antiphon': 'ANTYFONA NA WEJŚCIE'},
}
with tempfile.TemporaryDirectory() as temp:
    with patch.object(generator, 'OUTDIR', Path(temp)), \
         patch.object(generator, 'fetch_offices', return_value=ordinary), \
         patch.object(generator, 'fetch_source',
             side_effect=lambda day, suffix: (generator.source_url(day, suffix), dict(src))), \
         patch.object(generator, 'make_chants', return_value={}):
        generator.produce(DAY_27, replace=True)
    output = json.loads((Path(temp)/'2026-10-27.json').read_text(encoding='utf-8'))
    assert output['date'] == '2026-10-27'
    assert output['schema_version'] == 2
    assert output['default_office_id'] == 'zwykly-0'
    assert output['source_url'] == 'https://brewiarz.pl/x_26/2710/czyt.php3'
    assert output['celebration'] == 'Wtorek XXX tygodnia Okresu Zwykłego'
    assert len(output['songs']) == 5

print('OK: adresy ILG: zwykły /ddmm/, święto /ddmmp/ i obchód lokalny /ddmmw/')
