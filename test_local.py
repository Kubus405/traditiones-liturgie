"""Offline smoke test with a miniature 20 Oct 2026 HTML fixture."""
import datetime as dt
import json
from pathlib import Path
from generate_daily import parse_source_html, source_url, compose
from song_catalog import SONGS
from prefaces import choose_prefaces, easter_date, season
from chant_notation import make_chants

html = '''<html><head><title>.:ILG:. - 20 października 2026: CZYTANIA LITURGICZNE</title></head><body>
<p>Kolor szat: Wtorek, 20 października 2026 ŚW. JANA KANTEGO, PREZBITERA Wspomnienie obowiązkowe</p>
<p>ANTYFONA NA WEJŚCIE</p><p>Syr 18, 13. 14</p>
<p>Miłosierdzie Boga obejmuje wszystkich.</p><p>KOMENTARZ DO ANTYFONY</p>
<p>PIERWSZE CZYTANIE Chrystus jest naszym pokojem</p><p>Ef 2, 12-22</p><p>PIERWSZE ZDANIE</p>
<p>PSALM RESPONSORYJNY Ps 85 (84), 9ab i 10. 11-12.</p><p>Refren</p>
<p>ŚPIEW PRZED EWANGELIĄ Por. Łk 21, 36</p><p>Alleluja</p>
<p>EWANGELIA Oczekiwanie powrotu Pana</p><p>Łk 12, 35-38</p><p>Oto słowo Pańskie.</p>
</body></html>'''
day = dt.date(2026, 10, 20)
parsed = parse_source_html(day, html)
assert parsed['ref']['readings'] == 'Ef 2, 12-22', parsed
assert parsed['ref']['gospel'] == 'Łk 12, 35-38', parsed
assert parsed['theme'] == 'miłosierdzie', parsed
assert parsed['saint_name'].startswith('Św. '), parsed
content = compose(day, source_url(day), parsed)
assert content['date'] == '2026-10-20'
assert len(content['intercessions']['petitions']) == 5
assert content['intercessions']['introduction']
assert content['intercessions']['conclusion'].endswith('Amen.')
assert len(content['songs']) == 5
assert content['second_reading_reference'] == ''
assert [p['number'] for p in content['prefaces']][:3] == [73, 70, 71]
assert all(p['number'] and p['name'] for p in content['prefaces'])
assert 'first_reading' in content['chant'] and 'gospel' in content['chant']
assert content['chant']['gospel']['is_full_text'] is False
assert (Path(__file__).parent / 'site' / content['chant']['gospel']['image']).is_file()
assert (Path(__file__).parent / 'site' / content['chant']['first_reading']['gabc']).is_file()
assert [p['number'] for p in choose_prefaces(dt.date(2026,10,25),'XXX niedziela zwykła')[0]] == list(range(28,36))
assert season(dt.date(2026,12,15)) == 'advent'
assert easter_date(2026) == dt.date(2026,4,5)
for slot, song in content['songs'].items():
    assert (slot, song['number'], song['title']) in {(s, n, t) for s, n, t, _ in SONGS}
assert 'OPENAI_API_KEY' not in Path(__file__).with_name('generate_daily.py').read_text()
print('OK: kalendarz, prefacje z numerami, GABC, PNG, modlitwa wiernych i katalog śpiewów')

# A Saturday / Sunday reading with a second lesson must preserve it.
second_fixture = html.replace('<p>PSALM RESPONSORYJNY',
    '<p>DRUGIE CZYTANIE</p><p>1 Kor 12, 1-10</p><p>PSALM RESPONSORYJNY')
# The source layout might put second reading after the Psalm; the parser must
# never silently invent or omit an explicit second reading.
second_parsed = parse_source_html(day, second_fixture)
assert second_parsed['ref']['second_reading'] == '1 Kor 12, 1-10'
second_content = compose(day, source_url(day), second_parsed)
assert 'second_reading' in second_content['chant']

assert season(dt.date(2022, 11, 27)) == 'advent'  # Boże Narodzenie w niedzielę
assert season(dt.date(2026, 1, 9)) == 'christmas'

# Do not leave the sample second-reading score in the public site; its sample
# date has no second reading. It was created only to test optional support.
for extra in ('drugie_czytanie.gabc', 'drugie_czytanie.png'):
    sample_extra = Path(__file__).parent / 'site' / 'neumy' / day.isoformat() / extra
    if sample_extra.exists():
        sample_extra.unlink()
