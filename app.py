import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja bazy danych
DATABASE_NAME = 'bip_job_offers.db'

# --- FUNKCJE BAZY DANYCH ---

@st.cache_data
def load_data():
    """Wczytuje wszystkie dane z bazy danych do ramki Pandas."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        # Sortowanie, aby najnowsze oferty były na górze
        df = pd.read_sql_query("SELECT * FROM offers ORDER BY data_dodania DESC", conn)
        conn.close()
        return df
    except sqlite3.OperationalError:
        st.error(f"Błąd bazy danych: Plik '{DATABASE_NAME}' nie został znaleziony. Upewnij się, że skrypt Fazy 2 zadziałał.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Wystąpił nieznany błąd podczas ładowania danych: {e}")
        return pd.DataFrame()

# --- FUNKCJE INTERFEJSU ---

def main_app():
    """Główny układ aplikacji Streamlit."""
    st.set_page_config(layout="wide", page_title="Lokalny Monitor Ofert Pracy BIP")

    st.title("🔎 Lokalny Monitor Ofert Pracy BIP")
    st.markdown("Ostatnio zaktualizowane oferty z portali Biuletynu Informacji Publicznej (BIP).")
    st.markdown("---")

    # Wczytanie danych
    df = load_data()

    if df.empty:
        return

    st.sidebar.header("Filtr Ofert")

    # 1. FILTROWANIE PO SŁOWACH KLUCZOWYCH
    search_query = st.sidebar.text_input(
        "Szukaj w Tytule",
        placeholder="np. informatyk, księgowy, specjalista"
    )

    # Przygotowanie danych do filtrowania
    today = pd.to_datetime('today').normalize()
    df['wazne_do_date'] = pd.to_datetime(df['wazne_do'], errors='coerce')
    
    # Domyślne filtrowanie: usuwamy oferty, których termin już minął
    df_filtered = df[df['wazne_do_date'].isna() | (df['wazne_do_date'] >= today)]

    # 2. FILTROWANIE PO URL BIP
    bip_selection = st.sidebar.multiselect(
        "Filtruj po Portalu BIP",
        options=df['bip_url'].unique(),
        default=[]
    )
    
    # APLIKOWANIE FILTRÓW
    
    # Filtr słów kluczowych
    if search_query:
        df_filtered = df_filtered[
            df_filtered['tytul'].str.contains(search_query, case=False, na=False)
        ]
        
    # Filtr BIP
    if bip_selection:
        df_filtered = df_filtered[df_filtered['bip_url'].isin(bip_selection)]

    st.subheader(f"Znaleziono {len(df_filtered)} aktywnych ogłoszeń")
    st.caption(f"Łącznie w bazie: {len(df)} ogłoszeń (w tym archiwalne/przeterminowane).")
    st.markdown("---")
    
    # 3. PRZYGOTOWANIE WIDOKU TABELI

    # Tworzymy nową kolumnę z klikalnym linkiem
    df_filtered['Akcja'] = df_filtered.apply(
        lambda row: f"[Zobacz Ogłoszenie]({row['link_oferty']})",
        axis=1
    )
    
    # Wybieramy i zmieniamy nazwy kolumn do wyświetlenia
    df_display = df_filtered[[
        'tytul', 
        'wazne_do', 
        'bip_url', 
        'data_dodania',
        'Akcja'
    ]].copy()

    df_display.columns = [
        'Tytuł Ogłoszenia', 
        'Termin Składania', 
        'Źródło (BIP URL)', 
        'Data Dodania do Aplikacji',
        'Link'
    ]

    # Ustawiamy format daty
    df_display['Data Dodania do Aplikacji'] = df_display['Data Dodania do Aplikacji'].str.split().str[0]
    
    # 4. WYŚWIETLANIE TABELI
   # st.dataframe(
    #    df_display, 
     #   use_container_width=True,
      #  hide_index=True,
        # Umożliwienie renderowania Markdown (klikanych linków) w kolumnie 'Link'
       # column_config={
        #    "Link": st.column_config.Column("Link", width="small")
        #}
    #)


# 4. WYŚWIETLANIE TABELI za pomocą st.markdown (dla aktywnego linku)
    
    # Tworzymy łańcuch znaków Markdown z całej tabeli
    markdown_table = df_display.to_markdown(index=False)
    
    # Dodajemy tytuł, ponieważ st.markdown zastępuje st.dataframe
    st.subheader("Wyniki wyszukiwania")

    # Wyświetlamy tabelę jako Markdown
    st.markdown(markdown_table, unsafe_allow_html=False)

    # Wróć do oryginalnego st.dataframe, jeśli masz bardzo dużo danych (tysiące wierszy),
    # ponieważ st.markdown może być mniej wydajny dla dużych tabel.
    # Jeśli jednak chcesz, aby linki były klikalne, ta metoda jest najprostsza.


if __name__ == "__main__":
    main_app()
