"""Offline regression tests for the office picker and the new songs data."""
import datetime as dt
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from office_catalog import parse_offices, office_color
from song_catalog import choose_songs, SONGS, LATIN_SONGS
import generate_daily as generator

DAY = dt.date(2026, 10, 22)
INDEX = '''<html><head><title>.:ILG:. - 22 października 2026</title></head>
<body><h2>WYBIERZ OFICJUM:</h2>
<p><a href="/x_26/2210p/index.php3?l=i">Wspomnienie obowiązkowe św. Jana Pawła II, papieża</a></p>
<p>W Wadowicach, Kalwarii Zebrzydowskiej, Świdnicy:
<a href="/x_26/2210w1/index.php3?l=i">UROCZYSTOŚĆ ŚW. JANA PAWŁA II, PAPIEŻA</a></p>
<p>W powiatach tatrzańskim i strzyżowskim:
<a href="/x_26/2210w1/index.php3?l=i">UROCZYSTOŚĆ ŚW. JANA PAWŁA II, PAPIEŻA</a></p>
<p>W II Zakonie Franciszkańskim:
<a href="/x_26/2210w2/index.php3">Wspomnienie dowolne bł. Józefiny Leroux, dziewicy i męczennicy</a></p>
<p>W diecezji sandomierskiej:
<a href="/x_26/2210w3/index.php3">ŚWIĘTO ROCZNICY POŚWIĘCENIA BAZYLIKI KATEDRALNEJ W SANDOMIERZU</a></p>
<p>W bazylice katedralnej w Sandomierzu:
<a href="/x_26/2210w4/index.php3">UROCZYSTOŚĆ ROCZNICY POŚWIĘCENIA BAZYLIKI KATEDRALNEJ W SANDOMIERZU</a></p>
<p>Poza Polską: <a href="/x_26/2210w5/index.php3">Czwartek XXIX tygodnia Okresu Zwykłego</a></p>
<p>Poza Polską: <a href="/x_26/2210p/index.php3">Wspomnienie dowolne św. Jana Pawła II</a></p>
</body></html>'''

items = parse_offices(DAY, INDEX)
assert len(items) == 8
assert items[0]['source_code'] == 'p'
assert items[1]['scope'].startswith('W Wadowicach')
assert items[2]['scope'].startswith('W powiatach')
assert items[3]['color'] == 'czerwony'
assert items[4]['color'] == 'biały'
assert items[6]['color'] == 'zielony'
assert items[-1]['scope'] == 'Poza Polską'
assert len({x['id'] for x in items}) == len(items)

# On ordinary days with no office picker, the default Mass remains available.
assert parse_offices(DAY, '''<html><title>22 października 2026</title><p>Nie ma wyboru.</p></html>''')[0]['source_code'] == 'p'
assert office_color('Wspomnienie św. Jana Pawła II, papieża', DAY)[0] == 'biały'

for i in range(15):
    date = DAY + dt.timedelta(days=i)
    selections = choose_songs(['miłość', 'eucharystia', 'dziękczynienie'], date)
    assert len(selections) == 5
    for slot, value in selections.items():
        assert len(value['polish']) == 3
        assert len({s['number'] for s in value['polish']}) == 3
        assert all((slot, s['number'], s['title']) in
                   {(a,b,c) for a,b,c,_ in SONGS} for s in value['polish'])
        assert value['latin']['title'] in [s[0] for s in LATIN_SONGS[slot]]
        assert value['latin']['number'] == ''  # never fabricate a number

src = {
  'theme': 'wiara',
  'saint_name': 'Św. Jan Paweł Ii',
  'celebration': 'Wspomnienie obowiązkowe św. Jana Pawła II, papieża',
  'ref': {'readings': 'Ef 3, 2-12', 'second_reading': '',
          'psalm': 'Ps 33, 1-2', 'acclamation': 'Łk 21, 36', 'gospel': 'Łk 12, 39-48'},
  'sections': {'antiphon': 'ANTYFONA NA WEJŚCIE', 'readings': 'PIERWSZE CZYTANIE'},
}
with tempfile.TemporaryDirectory() as temp:
    with patch.object(generator, 'OUTDIR', Path(temp)), \
         patch.object(generator, 'fetch_offices', return_value=items), \
         patch.object(generator, 'fetch_source',
             side_effect=lambda day, suffix: (generator.source_url(day,suffix), src)), \
         patch.object(generator, 'make_chants', return_value={}):
        generator.produce(DAY, replace=True)
        data = json.loads((Path(temp)/'2026-10-22.json').read_text(encoding='utf-8'))
        assert data['schema_version'] == 2
        assert data['date'] == '2026-10-22'
        assert len(data['offices']) == 8
        assert data['default_office_id'] == 'p-0'
        assert data['offices'][0]['data']['date'] == data['date']
        assert data['offices'][1]['data']['reading_url'].endswith('2210w1/czyt.php3')
        assert data['offices'][1]['data'] == data['offices'][2]['data']
        assert 'reading_text' not in str(data)
print('OK: 8 opcji, 5 x (3 PL + 1 LA), kolory, źródła i JSON v2')
