from bs4 import BeautifulSoup
import requests
import sqlite3
import time
from datetime import datetime
import re

# --- KONFIGURACJA ---
DATABASE_NAME = 'bip_job_offers.db'
BIP_LIST_FILENAME = 'bip_list.txt'
OFFERS_PATH = '/search/joboffers/'

# --- FUNKCJE BAZY DANYCH ---

def setup_database():
    """Tworzy bazę danych i tabelę 'offers', jeśli nie istnieją."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY,
            tytul TEXT NOT NULL,
            link_oferty TEXT UNIQUE NOT NULL, -- Zapobiega duplikatom
            bip_url TEXT NOT NULL,
            data_publikacji TEXT,
            wazne_do TEXT,
            data_dodania DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Baza danych gotowa.")

def insert_offer(offer_data):
    """Wstawia pojedynczą ofertę do bazy danych, ignorując duplikaty."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # data_publikacji jest na sztywno ustawiona na dziś, bo jej nie ma w liście
        cursor.execute('''
            INSERT INTO offers (tytul, link_oferty, bip_url, wazne_do, data_publikacji)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            offer_data['tytul'], 
            offer_data['link_oferty'], 
            offer_data['bip_url'], 
            offer_data['wazne_do'],
            offer_data.get('data_publikacji', datetime.now().strftime('%Y-%m-%d'))
        ))
        conn.commit()
        return True # Wstawiono
    except sqlite3.IntegrityError:
        # Ignorujemy błąd, jeśli oferta już istnieje (na podstawie unikalnego link_oferty)
        return False # Duplikat
    finally:
        conn.close()

# --- GŁÓWNA FUNKCJA SCRAPUJĄCA ---

def scrape_bip_offers():
    """Iteruje przez BIP-y, scrapuje oferty i zapisuje je do bazy danych."""
    
    # 1. Odczytanie listy BIP-ów
    try:
        with open(BIP_LIST_FILENAME, 'r', encoding='utf-8') as f:
            bip_urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"🛑 Błąd: Plik {BIP_LIST_FILENAME} nie został znaleziony.")
        return

    print(f"\n--- Rozpoczynanie scrapowania ofert z {len(bip_urls)} portali BIP ---")
    total_new_offers = 0

    # 2. Iteracja przez wszystkie BIP-y
    for i, base_url in enumerate(bip_urls, 1):
        
        # Upewniamy się, że base_url nie ma ukośnika na końcu, aby poprawnie zbudować URL
        base_url = base_url.rstrip('/') 
        job_offers_base_url = base_url + OFFERS_PATH

        print(f"\n[{i}/{len(bip_urls)}] 🌐 Sprawdzanie: {base_url}")
        
        new_offers_count_for_bip = 0
        page_num = 1
        
        while True:
            # Tworzymy URL z paginacją (struktura paginacji jest taka sama dla ofert jak dla listy BIP)
            url_to_scrape = job_offers_base_url if page_num == 1 else f"{job_offers_base_url}page:{page_num}"
            
            try:
                response = requests.get(url_to_scrape, timeout=15)
                
                # Jeśli strona z ofertami nie istnieje, przechodzimy do kolejnego BIP-u
                if response.status_code == 404:
                    print("   [INFO] Strona z ofertami nie istnieje (404). Pomijam ten BIP.")
                    break
                    
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # UŻYJEMY STRUKTURY TABELI Z OFERTAMI: table.wyniki_szukania tr.color
                offers_rows = soup.select('table.wyniki_szukania tr.color')
                
                if not offers_rows:
                    if page_num > 1:
                       print(f"   [INFO] Brak kolejnych ofert na stronie {page_num}. Koniec dla tego BIP-u.")
                    else:
                        print("   [INFO] Nie znaleziono ofert na stronie 1.")
                    break
                
                # 3. Ekstrakcja danych z każdego wiersza
                for row in offers_rows:
                    # Szukamy kolumn (td)
                    columns = row.find_all('td')
                    
                    # Oczekujemy 5 kolumn w wierszu oferty (1, Tytuł, Stanowisko, Termin, Zobacz)
                    if len(columns) < 5:
                        continue 
                        
                    # Kolumna 2 (indeks 1) zawiera link i tytuł w <a>
                    link_element = columns[1].find('a')
                    
                    if link_element:
                        tytul = link_element.text.strip()
                        
                        # Link jest relatywny, musimy go zamienić na absolutny
                        relative_link = link_element.get('href')
                        full_offer_link = base_url + relative_link 
                        
                        # Kolumna 4 (indeks 3) zawiera termin składania
                        wazne_do = columns[3].text.strip()
                        
                        offer_data = {
                            'tytul': tytul,
                            'link_oferty': full_offer_link,
                            'bip_url': base_url,
                            'wazne_do': wazne_do
                        }
                        
                        # 4. Zapis do bazy danych
                        if insert_offer(offer_data):
                            total_new_offers += 1
                            new_offers_count_for_bip += 1
                
                # --- Logika Paginacji Ofert ---
                # Szukamy linku do następnej strony w div.paging
                paging_div = soup.select_one('div.paging')
                has_next_page = False
                if paging_div:
                    # Szukamy linku z klasą 'next' lub z numerem strony większym niż obecna
                    # Uwaga: używamy formatu paginacji: /search/joboffers/page:2
                    next_link = paging_div.select_one(f'span a[href*="page:{page_num + 1}"], span a.next')
                    if next_link:
                        has_next_page = True

                print(f"   [INFO] Strona {page_num} - nowych: {new_offers_count_for_bip}. Kontynuacja: {'Tak' if has_next_page else 'Nie'}.")

                if has_next_page:
                    page_num += 1
                    time.sleep(1) # Odczekanie przed przejściem do kolejnej strony
                else:
                    break # Koniec paginacji dla tego BIP-u
                
            except requests.exceptions.RequestException as e:
                print(f"   🛑 Błąd HTTP/Połączenia dla {url_to_scrape}: {e}")
                break # Przechodzimy do kolejnego BIP-u
            except Exception as e:
                print(f"   🛑 Wystąpił nieoczekiwany błąd podczas przetwarzania {url_to_scrape}: {e}")
                break
        
        # Krótka przerwa między kolejnymi BIP-ami
        time.sleep(1) 

    print(f"\n*** ZAKOŃCZENIE ZBIORCZE ***")
    print(f"Łącznie dodano/zaktualizowano {total_new_offers} unikatowych ofert pracy.")
    print(f"Dane znajdują się w bazie **{DATABASE_NAME}**.")

# --- Uruchomienie Skryptu ---

if __name__ == "__main__":
    setup_database()
    scrape_bip_offers()