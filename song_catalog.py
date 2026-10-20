"""Whitelisted hymn titles, checked against the official Siedlecki XLI index.

No hymn lyrics are stored or reproduced. Editions / page numbers can vary;
'number' refers to the XLI numbered item, not a page.
https://spiewniksiedleckiego.pl/wp-content/uploads/spis_tresci_2015-1.pdf

Do not let an AI invent song titles or book affiliations. Add Śpiewnik
Liturgiczny and Droga do Nieba entries only after checking their indexes.
"""

SONGBOOK = 'Śpiewnik Siedleckiego, wyd. XLI'
SOURCE = 'https://spiewniksiedleckiego.pl/wp-content/uploads/spis_tresci_2015-1.pdf'

# slot, number, exact title, thematic keywords
SONGS = [
    ('entrance', '692', 'Gdzie miłość wzajemna', ['miłość', 'jedność', 'pokój', 'braterstwo', 'miłosierdzie']),
    ('entrance', '688', 'Boże, lud Twój', ['kościół', 'wspólnota', 'jedność', 'święci']),
    ('entrance', '608', 'Kto się w opiekę', ['opieka', 'zaufanie', 'wiara', 'cierpienie']),
    ('entrance', '605', 'Jak miłe przybytki', ['kościół', 'świątynia', 'wspólnota']),
    ('entrance', '199', 'Bądź uwielbiony, miłosierny Boże', ['miłosierdzie', 'przebaczenie']),
    ('entrance', '97', 'Bliskie jest królestwo Boże', ['pokuta', 'wielki post', 'nawrócenie']),
    ('entrance', '3', 'Oto Pan Bóg przyjdzie', ['adwent', 'oczekiwanie']),
    ('entrance', '37', 'Bóg się rodzi, moc truchleje', ['narodzenie pańskie', 'boże narodzenie']),
    ('entrance', '178', 'Chrystus Pan zmartwychwstał', ['wielkanoc', 'zmartwychwstanie']),
    ('entrance', '215', 'Duchu Najświętszy', ['zesłanie ducha', 'duch święty']),
    ('offertory', '694', 'Przyjmij, Boże, tę ofiarę', ['ofiara', 'dary', 'wspólnota', 'miłość']),
    ('offertory', '695', 'Przyjmij, o Najświętszy Panie', ['ofiara', 'dary', 'pokuta']),
    ('offertory', '696', 'Przyjmij, Ojcze, hostię białą', ['eucharystia', 'dary', 'wiara']),
    ('offertory', '697', 'Składamy Ci, Ojcze', ['dziękczynienie', 'ofiara', 'pokój']),
    ('offertory', '698', 'Stwórca chleba, Stwórca wina', ['eucharystia', 'stworzenie', 'dary']),
    ('communion', '264', 'Panie, dobry jak chleb', ['eucharystia', 'chleb', 'miłosierdzie', 'miłość']),
    ('communion', '273', 'Skosztujcie i zobaczcie', ['eucharystia', 'dobroć', 'zaufanie']),
    ('communion', '271', 'Przyjdźcie do mnie wszyscy', ['miłosierdzie', 'pokój', 'odpoczynek', 'miłość']),
    ('communion', '283', 'Zbliżam się w pokorze', ['eucharystia', 'wiara', 'pokuta']),
    ('communion', '233', 'Bądźże pozdrowiona', ['eucharystia', 'adoracja']),
    ('communion', '699', 'Panie, nie jestem godzien', ['eucharystia', 'pokora', 'nawrócenie']),
    ('thanksgiving', '701', 'Chrystus Pan karmi nas', ['eucharystia', 'dziękczynienie', 'miłość']),
    ('thanksgiving', '702', 'Dziękczynne pieśni śpiewajmy', ['dziękczynienie', 'wdzięczność']),
    ('thanksgiving', '703', 'Dzięki Ci, Panie', ['dziękczynienie', 'wdzięczność']),
    ('thanksgiving', '704', 'O Boże, dzięki Ci składamy', ['dziękczynienie', 'wdzięczność']),
    ('thanksgiving', '236', 'Chwała i dziękczynienie', ['dziękczynienie', 'adoracja']),
    ('recessional', '609', 'Niechaj z nami będzie Pan', ['pokój', 'zaufanie', 'droga']),
    ('recessional', '630', 'Wszystkie narody świata', ['misja', 'jedność', 'uwielbienie']),
    ('recessional', '222', 'Idźcie na cały świat', ['misja', 'ewangelizacja', 'apostoł']),
    ('recessional', '638', 'My chcemy Boga', ['wiara', 'kościół', 'odwaga']),
    ('recessional', '621', 'Przykazanie nowe daję wam', ['miłość', 'jedność', 'miłosierdzie']),
    ('recessional', '37', 'Bóg się rodzi, moc truchleje', ['narodzenie pańskie', 'boże narodzenie']),
    ('recessional', '193', 'Wesoły nam dzień dziś nastał', ['wielkanoc', 'zmartwychwstanie']),
]


def choose_songs(themes, date):
    """Choose one real, numbered song per slot; favor antiphon/season themes.

    No external language model can add to this catalog. Always return five slots.
    """
    cleaned = [str(t).lower().strip() for t in themes][:8]
    result = {}
    for slot in ('entrance', 'offertory', 'communion', 'thanksgiving', 'recessional'):
        candidates = [s for s in SONGS if s[0] == slot]
        # Tie-break rotation deterministic by date, but without obscuring theme.
        offset = date.toordinal() % len(candidates)
        rotated = candidates[offset:] + candidates[:offset]
        # The first theme is antiphon priority, then the other motifs.
        def score(song):
            tags = song[3]
            value = sum((15 if i == 0 else 5) for i, theme in enumerate(cleaned)
                        if theme and theme in tags)
            # More relevant than thematic lyrics mismatched with the season.
            seasonal = {'adwent', 'narodzenie pańskie', 'boże narodzenie',
                        'wielki post', 'wielkanoc', 'zmartwychwstanie',
                        'zesłanie ducha', 'duch święty'}
            selected_seasons = set(cleaned) & seasonal
            if any(t in seasonal and t not in selected_seasons for t in tags):
                value -= 100
            return value
        choice = max(rotated, key=score)
        result[slot] = {
            'title': choice[2], 'book': SONGBOOK, 'number': choice[1],
            'catalog_url': SOURCE,
        }
    return result
