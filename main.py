import datetime
from typing import  TypedDict
from src.model.GameBackend import GameBackend
from src.database.init import *

class Player(TypedDict):
    id: str
    name: str
    

class Queue(TypedDict, total=False):
    id: str
    arrival: datetime.datetime
    name: str   # aggiunto come chiave opzionale

if __name__ == '__main__':
    backend = GameBackend()
    
    # Assicuriamoci che, al momento, non ci sia un game in corso
    # Aggiungiamo alcune coppie e alcuni singoli in coda
    # backend.add_couple("GIALLO-01")
    # backend.add_single("BLU-01")
    # backend.add_couple("GIALLO-02")
    # backend.add_single("BLU-02")
    # backend.add_couple("GIALLO-03")
    # backend.add_single("BLU-03")
    print("Tabellone Coppie (Gialli):")
    # Assicuriamoci che, al momento, non ci sia un game in corso
    now = datetime.datetime.now()
    backend.ALFA_next_available = now
    backend.BRAVO_next_available = now
    backend.ALFA2_next_available = now
    backend.BRAVO2_next_available = now
    # Otteniamo il tabellone d'attesa
    couples_board, singles_board, charlie_board, statico_board, couples2_board, singles2_board = backend.get_waiting_board()
    print("Tabellone Coppie (Gialli):")
    for pos, cid, time_est in couples_board:
      time_str = time_est.strftime('%H:%M:%S') if isinstance(time_est, datetime.datetime) else time_est if time_est else 'N/D'
    print(f"{pos}. {cid} - Ingresso stimato: {time_str}")
    print("\nTabellone Coppie (Blu):")
    for pos, cid, time_est in couples2_board:
      time_str = time_est.strftime('%H:%M:%S') if isinstance(time_est, datetime.datetime) else time_est if time_est else 'N/D'
    print(f"{pos}. {cid} - Ingresso stimato: {time_str}")
    print("\nTabellone Singoli (Blu):")
    for pos, sid, time_est in singles_board:
      time_str = time_est.strftime('%H:%M:%S') if isinstance(time_est, datetime.datetime) else time_est if time_est else 'N/D'
    print(f"{pos}. {sid} - Ingresso stimato: {time_str}")
    print("\nTabellone Charlie (Verde):")
    for pos, cid, time_est in charlie_board:
      time_str = time_est.strftime('%H:%M:%S') if isinstance(time_est, datetime.datetime) else time_est if time_est else 'N/D'
    print(f"{pos}. {cid} - Ingresso stimato: {time_str}")
    print("\nTabellone Statico (Rosso):")
    for pos, cid, time_est in statico_board:
      time_str = time_est.strftime('%H:%M:%S') if isinstance(time_est, datetime.datetime) else time_est if time_est else 'N/D'
    print(f"{pos}. {cid} - Ingresso stimato: {time_str}")

