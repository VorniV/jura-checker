import requests
from bs4 import BeautifulSoup
import os
import hashlib
import sys

# --- KONFIGURATION ---
# Trage hier die echten Links zu den Jura-Seiten ein
URLS = [
    #"https://httpbin.org/uuid",
    "https://www.olg-hamm.nrw.de/aufgaben/geschaeftsverteilung/verwaltung/dez05-neu/01_Einstellungsverfahren/index.php",
    "https://www.olg-koeln.nrw.de/aufgaben/referendarabteilung/002_aktuelles/003_zw_aktuelles/001_restplaetze/index.php",
    "https://www.olg-duesseldorf.nrw.de/aufgaben/referendarabteilung/09_weiter_info/index.php",
]

# Secrets aus GitHub laden
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram Secrets fehlen!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"Fehler beim Senden der Nachricht: {e}")

def get_site_hash(url):
    """Lädt Seite und berechnet Hash vom Text-Inhalt"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Wir nehmen den gesamten Text der Seite.
        # Falls das zu viele Fehlalarme gibt, müsste man hier präziser filtern (z.B. soup.find('div', id='content'))
        text_content = soup.get_text()
        
        # Hash berechnen
        return hashlib.md5(text_content.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return None

def check_updates():
    changes_found = False
    
    for url in URLS:
        print(f"Prüfe: {url}")
        current_hash = get_site_hash(url)
        
        if not current_hash:
            continue
            
        # Dateinamen für den Hash basierend auf der URL erstellen (damit er eindeutig ist)
        url_id = hashlib.md5(url.encode()).hexdigest()
        filename = f"status_{url_id}.txt"
        
        # Alten Hash laden
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                old_hash = f.read().strip()
        else:
            old_hash = "NEU"

        # Vergleich
        if old_hash != current_hash:
            print(f"!!! ÄNDERUNG BEI {url} !!!")
            
            # Nachricht senden (außer beim allerersten Lauf, da ist es ja nur 'Initialisierung')
            if old_hash != "NEU":
                send_telegram(f"🚨 ÄNDERUNG ERKANNT!\n\nAuf der Seite:\n{url}\n\nEs könnten neue Plätze da sein!")
            else:
                print("Erster Lauf - speichere Status.")

            # Neuen Hash speichern
            with open(filename, 'w') as f:
                f.write(current_hash)
            
            changes_found = True
        else:
            print("Keine Änderung.")

    # Wenn Änderungen gefunden wurden, exit code setzen, damit git commit weiß, dass was passiert ist?
    # Nicht zwingend nötig, da wir dateien geändert haben.

if __name__ == "__main__":
    check_updates()
