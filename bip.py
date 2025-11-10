import requests
from bs4 import BeautifulSoup
import time
import re

# Stałe dla skryptu
BASE_URL = "https://ssdip.bip.gov.pl/search/graphsubjects/"
URL_SUFFIX = "state_id:25/substate_id:557" 
BIP_LIST_FILENAME = 'bip_list.txt'

bip_urls = set()
page_num = 1
max_pages_check = 20 # Zmienna ograniczająca pętlę na wypadek błędu w identyfikacji końca

print("🔍 Rozpoczynanie pobierania listy portali BIP...")

# Ustalenie, ile stron ma lista (z Twojego HTML wynika, że jest ich 17)
# Zmieniamy pętlę na while, która będzie szukać linku do ostatniej strony
last_page_element = None 
try:
    response = requests.get(f"{BASE_URL}{URL_SUFFIX}", timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Znajdujemy link 'last' i wyodrębniamy numer strony z atrybutu href
    last_page_link = soup.select_one('div.paging a.last')
    if last_page_link:
        # Przykładowy href: /search/graphsubjects/page:17/state_id:25/substate_id:557
        match = re.search(r'page:(\d+)', last_page_link.get('href', ''))
        if match:
            max_pages_check = int(match.group(1))
            print(f"Znaleziono całkowitą liczbę stron: {max_pages_check}.")
except Exception as e:
    print(f"Błąd przy próbie ustalenia max. stron: {e}. Używam domyślnego limitu {max_pages_check}.")

# Pętla iterująca po stronach
while page_num <= max_pages_check:
    # Używamy formatu URL z paginacją, który Pan podał
    url = f"{BASE_URL}page:{page_num}/{URL_SUFFIX}"
    if page_num == 1:
        url = f"{BASE_URL}{URL_SUFFIX}" # Strona 1 nie musi mieć page:1

    print(f"\n---> Przetwarzanie strony: {page_num} ({url})")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # CELUJEMY W WIERSZE Z DANYMI BIP-ÓW
        rows = soup.select('table.wyniki_szukania tr.color')
        
        new_links_count_on_page = 0
        
        if not rows:
            print("   [INFO] Brak wierszy z danymi. Koniec listy lub błąd parsowania.")
            break
            
        for row in rows:
            # Kolumny (td):
            # 0: numer
            # 1: Nazwa + Adres (tekst)
            # 2: Strona (link URL) <-- TEN CHCEMY
            # 3: Więcej
            
            columns = row.find_all('td')
            
            # Musimy mieć przynajmniej 3 kolumny, aby znaleźć adres
            if len(columns) > 2:
                # 3. Wyodrębnienie linku z trzeciej kolumny (indeks 2)
                link_element = columns[2].find('a')
                
                if link_element:
                    href = link_element.get('href')
                    
                    # Weryfikacja i normalizacja URL (upewnienie się, że link ma protokół i jest BIP-em)
                    if href and 'bip.gov.pl' in href and href.startswith('http'):
                         # W podanym HTML link jest już URL-em bazowym (np. http://agencjabadmed.bip.gov.pl)
                        base_url = href.strip()
                        
                        if base_url not in bip_urls:
                            bip_urls.add(base_url)
                            new_links_count_on_page += 1

        if new_links_count_on_page > 0:
            print(f"✅ Znaleziono {new_links_count_on_page} nowych adresów. Łącznie: {len(bip_urls)}.")
        else:
            print(f"⚠️ Nie znaleziono nowych adresów na tej stronie.")

    except requests.exceptions.RequestException as e:
        print(f"🛑 Błąd podczas pobierania strony {page_num}: {e}")
        break
    except Exception as e:
        print(f"🛑 Wystąpił nieoczekiwany błąd parsowania na stronie {page_num}: {e}")
        break

    page_num += 1
    time.sleep(0.5) # Krótki odstęp

# Zapisanie wyników do pliku
with open(BIP_LIST_FILENAME, 'w', encoding='utf-8') as f:
    for url in sorted(list(bip_urls)):
        f.write(url + '\n')

print(f"\n--- Zakończono Fazę 1 ---")
print(f"✅ Zapisano {len(bip_urls)} unikatowych adresów BIP do pliku **{BIP_LIST_FILENAME}**")