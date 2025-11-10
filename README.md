#  LOKALNY MONITOR OFERT PRACY BIP (Biuletyn Informacji Publicznej)

Lokalna aplikacja stworzona w Pythonie, przeznaczona do automatycznego pobierania, agregowania i monitorowania ofert pracy publikowanych na wszystkich zidentyfikowanych portalach Biuletynu Informacji Publicznej (BIP) w Polsce.

---

## Wymagania i Uruchomienie

Projekt składa się z trzech głównych faz:
1.  Pobranie pełnej listy portali BIP.
2.  Scrapowanie ofert pracy i zapis do bazy danych.
3.  Interfejs użytkownika (UI) do przeglądania wyników.

### 1. Wymagania Systemowe

Wymagany jest **Python 3.x**.

### 2. Instalacja Zależności

Przed uruchomieniem jakichkolwiek skryptów, zainstaluj wszystkie wymagane biblioteki:

```bash
pip install requests beautifulsoup4 pandas streamlit tabulate
````

### 3\. Faza 1 & 2: Scrapowanie Danych

Upewnij się, że masz pliki:

  * `scrape_bip_list.py` (Faza 1 - dla jednorazowego pobrania listy BIP-ów)
  * `scrape_offers.py` (Faza 2 - do regularnego pobierania ofert)

#### 3.1. Pobranie Listy BIP-ów (Jednorazowo)

Uruchom Fazy 1, aby utworzyć plik `bip_list.txt`.

```bash
python scrape_bip_list.py
```

#### 3.2. Pobieranie Ofert (Regularnie)

Uruchom Fazy 2. Spowoduje to utworzenie bazy danych `bip_job_offers.db` i wypełnienie jej ofertami z każdego portalu BIP.

```bash
python scrape_offers.py
```

> **Wskazówka:** Aby monitorować oferty na bieżąco, zalecane jest ustawienie **automatycznego harmonogramu** (np. `cron` na Linux/macOS lub **Harmonogram Zadań** na Windows), który uruchomi `scrape_offers.py` raz dziennie.

-----

##  Uruchomienie Interfejsu Użytkownika (Faza 3)

Interfejs użytkownika (UI) jest oparty na **Streamlit** i działa bezpośrednio na danych z bazy `bip_job_offers.db`.

### 1\. Uruchomienie Aplikacji

Uruchom plik `app.py` za pomocą Streamlit:

```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie w przeglądarce (zazwyczaj pod adresem `http://localhost:8501`).

### 2\. Funkcje Interfejsu

  * **Tabela:** Wyświetla wszystkie aktywne oferty pracy z bazy.
  * **Filtrowanie:** Lewy pasek boczny umożliwia filtrowanie po słowach kluczowych w tytule oraz po konkretnych adresach URL portali BIP.
  * **Aktywne Linki:** Kolumna "Link" zawiera **klikalne odnośniki** prowadzące bezpośrednio do pełnej treści ogłoszenia na stronie BIP.

-----

##  Architektura Projektu

| Komponent | Opis | Zastosowane Technologie |
| :--- | :--- | :--- |
| **Scraper** | Pobieranie list BIP i list ogłoszeń z `/search/joboffers/` | Python, `requests`, `BeautifulSoup` |
| **Baza Danych** | Trwałe przechowywanie zebranych ofert (tytuł, link, termin składania) | **SQLite** (`bip_job_offers.db`) |
| **Interfejs UI** | Interaktywny pulpit do przeglądania i filtrowania danych | **Streamlit**, `pandas` |

```
```
