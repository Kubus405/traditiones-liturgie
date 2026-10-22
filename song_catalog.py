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


# Traditional Latin titles; no lyrics or unverified hymnbook numbers.
# The Latin song is NOT advertised as belonging to the three Polish books.
LATIN_SONGS = {
    'entrance': [
        ('Adeste fideles', ['narodzenie pańskie', 'boże narodzenie']),
        ('Veni Creator Spiritus', ['duch święty', 'zesłanie ducha']),
        ('Regina caeli', ['wielkanoc', 'zmartwychwstanie']),
        ('Gaudete in Domino semper', ['radość', 'adwent']),
        ('Ubi caritas', ['miłość', 'wspólnota', 'jedność']),
        ('Salve Regina', ['maryja', 'najświętszej maryi']),
        ('Laudate Dominum omnes gentes', ['uwielbienie', 'wiara']),
    ],
    'offertory': [
        ('Veni Creator Spiritus', ['duch święty', 'zesłanie ducha']),
        ('Ubi caritas', ['miłość', 'wspólnota', 'jedność']),
        ('Ave Maria', ['maryja', 'najświętszej maryi']),
        ('Adoro te devote', ['eucharystia', 'wiara']),
        ('Laudate Dominum omnes gentes', ['uwielbienie']),
    ],
    'communion': [
        ('Adoro te devote', ['eucharystia', 'wiara']),
        ('Ave verum corpus', ['eucharystia', 'ciało']),
        ('Panis angelicus', ['eucharystia', 'chleb']),
        ('Ubi caritas', ['miłość', 'wspólnota']),
    ],
    'thanksgiving': [
        ('Anima Christi', ['eucharystia', 'dziękczynienie']),
        ('Laudate Dominum omnes gentes', ['uwielbienie', 'radość']),
        ('Te Deum laudamus', ['dziękczynienie', 'radość']),
        ('Adoro te devote', ['eucharystia', 'wiara']),
    ],
    'recessional': [
        ('Salve Regina', ['maryja', 'najświętszej maryi']),
        ('Regina caeli', ['wielkanoc', 'zmartwychwstanie']),
        ('Alma Redemptoris Mater', ['adwent', 'narodzenie pańskie']),
        ('Ave Regina caelorum', ['wielki post']),
        ('Laudate Dominum omnes gentes', ['uwielbienie', 'radość']),
        ('Te Deum laudamus', ['dziękczynienie']),
    ],
}


def choose_songs(themes, date):
    """Three catalogued Polish items and one Latin title for each Mass slot.

    Does not invent catalogue numbers or claim liturgical approval.
    """
    cleaned = [str(t).lower().strip() for t in themes][:8]
    result = {}
    used_latin_titles = set()  # One Latin hymn may only appear once per Mass.
    seasonal = {'adwent', 'narodzenie pańskie', 'boże narodzenie',
                'wielki post', 'wielkanoc', 'zmartwychwstanie',
                'zesłanie ducha', 'duch święty'}
    selected_seasons = set(cleaned) & seasonal
    for slot in ('entrance', 'offertory', 'communion', 'thanksgiving', 'recessional'):
        candidates = [s for s in SONGS if s[0] == slot]
        offset = date.toordinal() % len(candidates)
        rotated = candidates[offset:] + candidates[:offset]

        def score(song):
            tags = song[3]
            value = sum((15 if i == 0 else 5) for i, theme in enumerate(cleaned)
                        if theme and theme in tags)
            if any(t in seasonal and t not in selected_seasons for t in tags):
                value -= 100
            return value

        ranked = sorted(rotated, key=score, reverse=True)
        polish = [{
            'title': song[2], 'book': SONGBOOK, 'number': song[1],
            'catalog_url': SOURCE, 'language': 'pl',
        } for song in ranked[:3]]
        assert len(polish) == 3
        latin_options = LATIN_SONGS[slot]
        loffset = date.toordinal() % len(latin_options)
        latin_rotated = latin_options[loffset:] + latin_options[:loffset]
        def latin_score(song):
            title, tags = song
            value = sum((15 if i == 0 else 5) for i, theme in enumerate(cleaned)
                        if theme and theme in tags)
            # Seasonal Marian antiphons and Advent/Christmas/Easter chants
            # are not generic fillers for an unrelated October Mass.
            restricted = {
                'Adeste fideles': {'narodzenie pańskie', 'boże narodzenie'},
                'Regina caeli': {'wielkanoc', 'zmartwychwstanie'},
                'Gaudete in Domino semper': {'adwent'},
                'Alma Redemptoris Mater': {'adwent', 'narodzenie pańskie', 'boże narodzenie'},
                'Ave Regina caelorum': {'wielki post'},
            }
            required = restricted.get(title)
            if required and not (set(cleaned) & required):
                value -= 100
            return value

        # Don't recommend the same chant for multiple moments of the Mass.
        unused_latin = [song for song in latin_rotated
                        if song[0].casefold().strip() not in used_latin_titles]
        if not unused_latin:
            raise ValueError(f'Brak niepowtarzających się śpiewów łacińskich dla: {slot}')
        latin = max(unused_latin, key=latin_score)
        used_latin_titles.add(latin[0].casefold().strip())
        result[slot] = {
            'polish': polish,
            'latin': {
                'title': latin[0], 'book': 'Tradycyjny śpiew łaciński',
                'number': '', 'language': 'la',
                'note': 'Dobór orientacyjny — sprawdź zgodność z formularzem i przepisami.',
            },
            # Older APKs still display one verified numbered Polish song.
            'title': polish[0]['title'], 'book': polish[0]['book'],
            'number': polish[0]['number'],
        }
    return result
