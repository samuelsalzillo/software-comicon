import requests

# URL della tua API PHP su Aruba
url = "https://www.mercenarisocs.it/k1Nwe3ALeyoe53fj/api.php"

try:
    # Tento la connessione
    response = requests.get(url)
    response.raise_for_status()

    json_data = response.json()

    if json_data["success"]:
        dati = json_data["data"]
        for riga in dati:
            print(riga)
    else:
        print(f"Errore dall'API: {json_data.get('error', 'Errore sconosciuto')}")

except requests.RequestException as e:
    print(f"Errore nella richiesta: {e}")