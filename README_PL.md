# Traditiones — automatyczne Liturgie **bez płatnego API**

Ta wersja **nie używa sztucznej inteligencji ani płatnego API**. Codziennie o 04:17 (Polska) GitHub Actions pobiera datowaną stronę kalendarza liturgicznego ze źródła `brewiarz.pl`, ustala obchód i sigla, układa oryginalne, krótkie pomoce **według szablonów** oraz wybiera pięć tytułów pieśni z dopuszczonego katalogu. Następnie GitHub Pages udostępnia JSON pobierany przez zakładkę **Liturgie** aplikacji Traditiones.

**Co rzeczywiście zawiera:** obchód dnia, temat antyfony (bez pełnego tekstu), szablonowe wprowadzenie, ewentualne wspomnienie świętego, sigla i odsyłacz do oryginalnych czytań, psalmu, aklamacji i Ewangelii, modlitwę wiernych (wstęp, pięć wezwań, zakończenie), oraz pięć śpiewów na wejście, przygotowanie darów, Komunię, uwielbienie i wyjście.

**Ważne ograniczenia:** to nie jest codzienna autorska homilia ani szczegółowe streszczenie Biblii. Wprowadzenia i wezwania opierają się na ograniczonych szablonach — nie udajemy, że to codziennie przygotowywane komentarze przez człowieka. Aktualnie katalog śpiewów zawiera tylko pozycje ze **Śpiewnika Siedleckiego XLI**; można dołożyć zweryfikowane pozycje z „Drogi do Nieba” i „Śpiewnika Liturgicznego”. Brak zgody na republikację oficjalnych pełnych tekstów: antyfona, czytania, psalm, aklamacja i Ewangelia pozostają **pod linkiem źródłowym**. Źródło musi być dostępne, w przeciwnym razie dany dzień nie zostanie opublikowany; harmonogram GitHub może czasem się opóźnić. Przed użyciem modlitw podczas Mszy celebrans powinien je zatwierdzić. Lokalny kalendarz diecezji może być inny.

## Uruchomienie — poprowadzimy to razem

1. Załóż bezpłatne konto na **https://github.com/** (jeśli masz, użyj obecnego).
2. Utwórz **publiczne repozytorium** o nazwie `traditiones-liturgie`.
3. Wgraj **zawartość folderu** `traditiones_bez_oplat` z ZIP-a do głównego katalogu repozytorium. Zachowaj dokładnie `.github/workflows/daily-liturgie.yml` oraz `site/.nojekyll`. Najwygodniej jest dodać pliki przez GitHub Desktop lub komendą Git (wyjaśnimy krok po kroku).
4. Na stronie repozytorium: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. W **Actions** uruchom ręcznie workflow `Codzienne liturgie Traditiones — bez płatnego API` (Run workflow) i sprawdź wynik.
6. W aplikacji w zakładce **Liturgie** kliknij ⚙️ i wpisz adres `https://TWOJ_LOGIN.github.io/traditiones-liturgie` (podmień login na swój). Aplikacja sama zacznie pobierać dane na kolejne dni.

**Nie wpisujesz żadnego klucza API, nie podajesz karty i nie wykupujesz usługi.** Na moment przygotowania instrukcji publiczne repozytoria korzystają z GitHub Actions i Pages bezpłatnie, w granicach zasad usługi. Po 60 dniach braku aktywności w publicznym repozytorium GitHub może automatycznie wyłączyć harmonogram; wtedy trzeba go znów włączyć. Nie należy podawać w repozytorium danych prywatnych.

Przygotowane pliki można przetestować lokalnie, jeśli jest zainstalowany Python 3:

```sh
pip install -r requirements.txt
python test_local.py
python generate_daily.py --days 1
```

Źródła: <https://brewiarz.pl> (tylko ustalenie dnia i siglów, bez publikowania pełnych tekstów), <https://spiewniksiedleckiego.pl/wp-content/uploads/spis_tresci_2015-1.pdf> (katalog tytułów i numerów). GitHub Pages: <https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages>.

## NOWE: prefacje oraz śpiewane czytania / Ewangelia (bez opłat)

Ta wersja ZIP zawiera dodatkowo:

- `prefaces.py`: **numery Mszału, nazwy możliwych prefacji, bez tekstów**. Na przykład we wspomnienie św. Jana Kantego, prezbitera, proponuje nr 73 (o świętych pasterzach), 70–71 (o świętych), a także 36–41 (zwykłe) jako możliwości zależne od formularza. Automatyzacja nie zastępuje mszału ani Ordo. Jeśli obchód może mieć prefację własną, program zamiast zgadywać informuje, że trzeba ją sprawdzić. Bierze pod uwagę ogólny rok liturgiczny, nie wszystkie kalendarze lokalne.
- `chant_notation.py`: każdego dnia bezpłatnie przygotowuje pliki `gabc` oraz obrazy `png` **kwadratowych nut na czterolinii** do czytania i Ewangelii. Flutter pokazuje PNG z możliwością powiększenia. Narzędzie generuje **schemat intonacji**, NIE autoryzowaną melodię liturgiczną; nie wolno stosować bez sprawdzenia przez kantora lub osobę odpowiedzialną za śpiew.
- Opcjonalnie na dzień z drugim czytaniem (np. niedzielę) dochodzi osobna partia drugiego czytania.
- `site/dni/YYYY-MM-DD.json` zawiera nowe pola `prefaces`, `prefaces_note` oraz `chant`. Obrazy trafiają do `site/neumy/YYYY-MM-DD/`, pliki źródłowe `gabc` do tej samej lokalizacji.

### Dlaczego w neumy nie wstawiamy automatycznie pełnego tekstu biblijnego?

Polskie przekłady i ich liturgiczne opracowania mogą podlegać prawu autorskiemu. Bez wyjaśnienia uprawnień plik źródłowy dostarcza **tylko schemat neumy** podpisany w aplikacji: „wzór, bez pełnego tekstu”. Pełny tekst pozostaje pod linkiem do źródła. Nie należy mylić wzoru z gotową partyturą śpiewanego czytania.

Jeśli posiadasz prawo do publikacji pełnych tekstów, możesz dodać plik `authorized_texts/2026-10-20.json` o postaci:

```json
{
  "rights_confirmed": true,
  "first_reading": "Tutaj własny lub licencjonowany tekst pierwszego czytania...",
  "second_reading": "Jeżeli występuje...",
  "gospel": "Tutaj własny lub licencjonowany tekst Ewangelii..."
}
```

Wtedy generator umieści go pod nutami jako **automatyczny szkic recytacji**, nadal wymagający korekty akcentów, kadencji i zgodności z zasadami śpiewu liturgicznego. Bez tego pliku pozostają czytelne wzory. Nie kopiuj do publicznego repozytorium przekładów, których nie wolno publicznie udostępniać.

### Ważne dla obecnego projektu Flutter

Trzeba podmienić `lib/main.dart` na plik przesłany razem z nowym ZIP-em (osobny plik `main.dart`). Nowy plik odczytuje powyższe pola. Projekt korzysta z gotowego `Image.network`, więc do wyświetlania PNG nie jest potrzebny nowy pakiet Fluttera.

**Źródła numeracji prefacji:**
- https://biblia.kerygma.pl/eucharystia/prefacje (grupy nr 1–90)
- https://www.ordo.pallotyni.pl/index.php/mszal-rzymski/prefacje (nazwy i wskazówki użycia)

**Opis formatu zapisu:** https://gregorio-project.github.io/gabc/ — `gabc` jest darmową, otwartą notacją dla chorału; nasze grafiki PNG to czytelny podgląd schematu intonacji, a pliki `gabc` można następnie poprawiać i składać w Gregorio.

**Uwaga o dostępności:** przy automatycznym generowaniu strony źródłowej mogą zmienić układ lub zablokować pobieranie, a darmowy harmonogram GitHub może się opóźnić. Samo pobranie ZIP-a nie uruchamia automatyzacji; repozytorium i GitHub Pages trzeba raz skonfigurować. W publicznym repozytorium i mieszcząc się w bezpłatnych limitach nie jest potrzebna karta ani płatne API.
