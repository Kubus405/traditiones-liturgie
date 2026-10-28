"""Fail a publishing job if today's verified liturgy JSON is missing.

This does not invent texts for days that ILG has not published.
"""
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

out = Path(__file__).resolve().parent / 'site' / 'dni'
day = dt.datetime.now(ZoneInfo('Europe/Warsaw')).date()
path = out / f'{day.isoformat()}.json'
if not path.is_file():
    sys.exit(f'BŁĄD: brak dzisiejszego pliku {path.name}. Sprawdź w logach "Wygeneruj" błędy odczytu ILG.')
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('date') != day.isoformat():
        raise ValueError('niezgodna data w JSON')
    if not data.get('celebration') or not isinstance(data.get('intercessions'), dict):
        raise ValueError('brak podstawowych danych liturgii')
    if not isinstance(data.get('songs'), dict) or len(data['songs']) != 5:
        raise ValueError('brak kompletu pięciu części śpiewu')
    if not isinstance(data.get('offices'), list) or not any('data' in x for x in data['offices']):
        raise ValueError('brak zweryfikowanego oficjum')
except (ValueError, OSError, json.JSONDecodeError) as exc:
    sys.exit(f'BŁĄD: niepoprawny dzisiejszy JSON {path.name}: {exc}')

print(f'OK: dzisiejsza liturgia {day.isoformat()} w {path.name}, '
      f'{len(data["offices"])} pozycji oficjum.')
for future in range(1, 4):
    nxt = day + dt.timedelta(days=future)
    if not (out / f'{nxt.isoformat()}.json').is_file():
        print(f'INFO: nie ma jeszcze liturgii przyszłej daty {nxt.isoformat()}')
