"""Create four-line square-note *draft* recitation aid images and GABC.

These formulas are educational aids, NOT officially promulgated tones or
verified accentuation. Scripture is included only when the repository operator
supplies authorized text with an explicit rights attestation.
"""
from pathlib import Path
import json
import re
import math
from xml.sax.saxutils import escape
import cairosvg
import pyphen

PL = pyphen.Pyphen(lang='pl_PL')
KIND = {
    'first_reading': ('Śpiewane pierwsze czytanie', 'czytanie', 'h'),
    'second_reading': ('Śpiewane drugie czytanie', 'drugie_czytanie', 'h'),
    'gospel': ('Śpiewana Ewangelia', 'ewangelia', 'j'),
}
EXAMPLE = 'Początek recytacja zakończenie.'
OUTDIR = Path(__file__).parent / 'site' / 'neumy'
AUTH_DIR = Path(__file__).parent / 'authorized_texts'


def _syllables(text):
    # Split tokens conservatively; pyphen handles Polish syllabification.
    tokens = re.findall(r"[\wĄĆĘŁŃÓŚŹŻąćęłńóśźż]+(?:[’'][\w]+)?[.,;:!?]?", text, flags=re.UNICODE)
    if not tokens:
        raise ValueError('Brak słów do notacji')
    result = []
    for word in tokens:
        parts = PL.inserted(word, hyphen='|').split('|')
        # Ensure punctuation stays with the last sung syllable.
        if not parts:
            continue
        for i, part in enumerate(parts):
            result.append((part, i == len(parts)-1, part[-1:] in '.!?', part[-1:] in ',;:'))
    return result


def _notes(kind, syllables):
    # Simple draft recitation formulas: stable reciting pitch with cadence.
    base = 3 if kind != 'gospel' else 5
    cadence = [base, base-1, base-2]
    notes = [base] * len(syllables)
    for index, (_, last, stop, pause) in enumerate(syllables):
        if stop:
            for delta, pitch in zip((-2, -1, 0), cadence):
                j = index + delta
                if j >= 0:
                    notes[j] = pitch
        elif pause:
            notes[index] = base-1
    return notes


def _gabc(title, syllables, notes):
    # Latin clef c4. Initial podatus and closing clivis add true two-note neumes.
    chars = 'efghijklm'
    header = [f'name: {title};', 'language: polski;',
              'commentary: Schemat recytacji, nie zatwierdzony ton liturgiczny;',
              '%%']
    out = ['(c4) ']
    for index, ((syl, last, end, pause), tone) in enumerate(zip(syllables, notes)):
        word = syl.replace('(', '').replace(')', '').replace('*', '')
        pitch = chars[max(0, min(len(chars)-1, tone))]
        if index == 0:
            pitch = chars[max(0, min(len(chars)-1, tone-1))] + pitch
        if end:
            pitch += chars[max(0, min(len(chars)-1, tone-1))]
        out.append(f'{word}({pitch}{"." if end else ""})')
        if end:
            out.append(' (::) ')
        elif pause:
            out.append(' (;) ')
        elif last:
            out.append(' ')
    return '\n'.join(header) + '\n' + ''.join(out).strip() + '\n'


def _svg(title, subtitle, syllables, pitches):
    width, inset, staff_right = 1300, 80, 1220
    note_gap = 44
    per_staff = max(1, (staff_right - inset) // note_gap)
    systems = math.ceil(len(syllables) / per_staff)
    # Increase if text samples are enormous. Drawing is chunked by notation rows.
    height = 165 + systems * 172 + 38
    font = 'DejaVu Sans, sans-serif'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="#fffdf9"/>',
             f'<text x="{inset}" y="54" font-family="{font}" font-size="31" font-weight="bold" fill="#292523">{escape(title)}</text>',
             f'<text x="{inset}" y="87" font-family="{font}" font-size="20" fill="#5f554c">{escape(subtitle)}</text>',
             f'<text x="{inset}" y="116" font-family="{font}" font-size="17" fill="#866448">Czterolinia • zapis kwadratowy • szkic, nie oficjalny ton</text>']
    for sys in range(systems):
        y = 154 + sys * 172
        for k in range(4):
            parts.append(f'<line x1="{inset}" y1="{y+k*16}" x2="{staff_right}" y2="{y+k*16}" stroke="#977d69" stroke-width="2"/>')
        # clef is displayed descriptively (instead of fake traditional letter engraving).
        parts.append(f'<text x="{inset+4}" y="{y+40}" font-size="31" font-family="{font}" fill="#88462c">C</text>')
        for j in range(per_staff):
            index = sys*per_staff+j
            if index >= len(syllables):
                break
            x = inset+72+j*note_gap
            sy, endword, endphrase, comma = syllables[index]
            pitch = pitches[index]
            # Each index corresponds to either a line or space in 4-line staff.
            # y+48 is bottom line, pitches 0..6 climb in 8px steps.
            ny = y+48 - pitch*8
            parts.append(f'<rect x="{x-8}" y="{ny-6}" width="15" height="11" rx="1" fill="#2e2924"/>')
            # A podatus at the start and clivis at the close, indicated also in GABC.
            if index == 0:
                parts.append(f'<line x1="{x+7}" y1="{ny-1}" x2="{x+17}" y2="{ny-8}" stroke="#2e2924" stroke-width="2"/>')
                parts.append(f'<rect x="{x+11}" y="{ny-13}" width="14" height="10" rx="1" fill="#2e2924"/>')
            if endphrase:
                parts.append(f'<line x1="{x+6}" y1="{ny}" x2="{x+15}" y2="{ny+9}" stroke="#2e2924" stroke-width="2"/>')
                parts.append(f'<rect x="{x+12}" y="{ny+4}" width="14" height="10" rx="1" fill="#2e2924"/>')
            if endphrase:
                parts.append(f'<line x1="{x+17}" y1="{y}" x2="{x+17}" y2="{y+48}" stroke="#8d3d20" stroke-width="3"/>')
            elif comma:
                parts.append(f'<line x1="{x+17}" y1="{y+18}" x2="{x+17}" y2="{y+48}" stroke="#8d3d20" stroke-width="2"/>')
            # Individual syllable text, not necessarily enough space for long words.
            disp = escape(sy)
            if len(sy) > 9:
                disp = escape(sy[:8]+'…')
            parts.append(f'<text x="{x}" y="{y+91}" font-family="{font}" text-anchor="middle" font-size="15" fill="#2e2924">{disp}</text>')
            if endword:
                parts.append(f'<circle cx="{x+16}" cy="{y+103}" r="1.2" fill="#d0c6b9"/>')
    parts.append('</svg>')
    return '\n'.join(parts)


def _authorized_text(day):
    """No scraping and republishing copyrighted biblical translations."""
    file = AUTH_DIR / f'{day.isoformat()}.json'
    if not file.is_file():
        return {}
    obj = json.loads(file.read_text(encoding='utf8'))
    if obj.get('rights_confirmed') is not True:
        raise ValueError(f'{file}: wymagane rights_confirmed=true, albo usuń plik')
    allowed = {}
    for field in KIND:
        value = obj.get(field, '')
        if not isinstance(value, str):
            raise ValueError(f'{file}: {field} musi być tekstem')
        value = value.strip()
        if len(value) > 6000:
            raise ValueError(f'{file}: {field} jest zbyt długie; podziel tekst na fragmenty')
        if value:
            allowed[field] = value
    return allowed


def make_chants(day, refs, *, outdir=OUTDIR):
    authorized = _authorized_text(day)
    result = {}
    directory = Path(outdir) / day.isoformat()
    directory.mkdir(parents=True, exist_ok=True)
    for field, (title, stem, _) in KIND.items():
        if field == 'second_reading' and not refs.get('second_reading'):
            continue
        text = authorized.get(field) or EXAMPLE
        has_full_text = field in authorized
        note = 'Robocza intonacja pełnego tekstu • wymaga korekty muzycznej' if has_full_text else 'Wzór intonacji — bez pełnego tekstu czytania'
        syllables = _syllables(text)
        notes = _notes(field, syllables)
        full_title = title
        svg = _svg(full_title, note, syllables, notes)
        png = directory / (stem + '.png')
        # PNG supported by Flutter without extra dependencies.
        cairosvg.svg2png(bytestring=svg.encode('utf8'), write_to=str(png), output_width=1100)
        gabc = directory / (stem + '.gabc')
        gabc.write_text(_gabc(full_title, syllables, notes), encoding='utf8')
        result[field] = {
            'title': title,
            'reference': refs.get(field, ''),
            'image': f'neumy/{day.isoformat()}/{stem}.png',
            'gabc': f'neumy/{day.isoformat()}/{stem}.gabc',
            'is_full_text': has_full_text,
            'status': 'Szkic automatyczny; niezweryfikowana akcentuacja i ton.',
        }
    return result
