# Author: Dario Arienzo
# Data: 07/05/2025
import requests

# URL della tua API PHP su Aruba
url = "https://www.mercenarisocs.it/k1Nwe3ALeyoe53fj/api.php"
def call_for_take_records():
    try:
        # Tento la connessione
        response = requests.get(url)
        response.raise_for_status()

        json_data = response.json()

        if json_data["success"]:
            dati = json_data["data"]
            return dati
        else:
            print(f"Errore dall'API: {json_data.get('error', 'Errore sconosciuto')}")
            return None

    except requests.RequestException as e:
        print(f"Errore nella richiesta: {e}")
        return None