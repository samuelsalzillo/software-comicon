import datetime
import sqlite3
from threading import Lock
import logging 
from copy import deepcopy
import pytz
from typing import List, Dict, TypedDict, Tuple, Optional, Union

class Player(TypedDict):
    id: str
    name: str
    

class Queue(TypedDict, total=False):
    id: str
    arrival: datetime.datetime
    name: str   # aggiunto come chiave opzionale

class GameBackend:
    def __init__(self) -> None:
        # Code: ogni elemento è un dizionario con "id" e "arrival" (orario d'arrivo)
        self.queue_couples: List[Queue] = []  # Es. [{'id': 'GIALLO-01', 'arrival': datetime}, ...]
        self.queue_singles: List[Queue] = []  # Es. [{'id': 'BLU-01', 'arrival': datetime}, ...]
        self.queue_couples2: List[Queue] = []  # Es. [{'id': 'ROSA-01', 'arrival': datetime}, ...]
        self.queue_singles2: List[Queue] = []  # Es. [{'id': 'ARANCIO-01', 'arrival': datetime}, ...]
        self.queue_charlie: List[Queue] = []  # Es. [{'id': 'VERDE-01', 'arrival': datetime}, ...]
        self.queue_statico: List[Queue] = []

        self.couples= []
        # Storico dei tempi (in minuti) registrati per aggiornamento dinamico
        self.couple_history_mid: List[float] = []    # Tempo dal Pulsante 1 al Pulsante 3 (liberazione di ALFA)
        # Update the history lists to store tuples of (player_id, score)
        self.couple_history_total: List[Tuple[str, float]] = []  # [(player_id, score), ...]
        self.single_history: List[Tuple[str, float]] = []        # [(player_id, score), ...]
        self.couple_history_mid2: List[float] = []    # Tempo dal Pulsante 1 al Pulsante 3 (liberazione di ALFA)
        self.couple_history_total2: List[Tuple[str, float]] = [] # [(player_id, score), ...]
        self.single_history2: List[Tuple[str, float]] = []       # [(player_id, score), ...]
        self.charlie_history: List[Tuple[str, float]] = []       # [(player_id, score), ...]
        self.statico_history: List[Tuple[str, float]] = []       # [(player_id, score), ...]

        self.charlie_timer_history: List[float] = []

        # Valori indicativi (default) iniziali (in minuti)
        self.default_T_mid = 2.0
        self.default_T_total = 5.0
        self.default_T_single = 2.0
        self.default_T_charlie = 3.0
        self.default_T_statico = 5.0

        # NUOVE Liste per le durate dei TIMER (usate per le medie)
        self.couple_timer_history: List[float] = []   # Durata timer per Coppie (Giallo + Rosa)
        self.single_timer_history: List[float] = []   # Durata timer per Singoli (Blu + Arancio)

        # Tempi attuali: partono dai valori indicativi e verranno aggiornati
        self.T_mid = self.default_T_mid
        self.T_total = self.default_T_total
        self.T_single = self.default_T_single
        self.T_charlie = self.default_T_charlie
        self.T_statico = self.default_T_statico

        # Giocatori attuali in pista
        self.current_player_alfa: Optional[Queue] = None
        self.current_player_bravo: Optional[Queue] = None
        self.current_player_alfa2: Optional[Queue] = None
        self.current_player_bravo2: Optional[Queue] = None
        self.current_player_charlie: Optional[Queue] = None
        self.current_player_delta: Optional[Queue] = None
        self.current_player_echo: Optional[Queue] = None

        # Stato iniziale delle piste: disponibilità immediata
        self.rome_tz = pytz.timezone('Europe/Rome')
        now = self.get_current_time()
        self.ALFA_next_available = now
        self.BRAVO_next_available = now
        self.ALFA_next_available2 = now
        self.BRAVO_next_available2 = now
        self.CHARLIE_next_available = now
        self.DELTA_next_available = now
        self.ECHO_next_available = now

        # Variabili per la gestione dei giocatori
        self.next_player_alfa_bravo_id: Optional[str] = None
        self.next_player_alfa_bravo_locked: bool = False
        self.next_player_alfa_bravo_name: Optional[str] = None
        self.next_player_alfa_bravo_id2: Optional[str] = None
        self.next_player_alfa_bravo_locked2: bool = False
        self.next_player_alfa_bravo_name2: Optional[str] = None
        self.next_player_charlie_id: Optional[str] = None
        self.next_player_charlie_locked: bool = False
        self.next_player_charlie_name: Optional[str] = None
        self.current_player_couple: Optional[Queue] = None
        self.current_player_couple2: Optional[Queue] = None
        self.player_in_charlie: bool = False
        self.next_player_statico_id: Optional[str] = None
        self.next_player_statico_locked: bool = False
        self.next_player_statico_name: Optional[str] = None

        # Flag per tracciare lo stato delle piste
        self.couple_in_bravo = False
        self.couple_in_alfa = False
        self.single_in_alfa = False
        self.third_button_pressed = False
        self.couple_in_bravo2 = False
        self.couple_in_alfa2 = False
        self.single_in_alfa2 = False
        self.third_button_pressed2 = False
        self.statico_in_delta = False
        self.statico_in_echo = False

        # Liste per i giocatori skippati
        self.skipped_couples: List[Queue] = []
        self.skipped_singles: List[Queue] = []
        self.skipped_couples2: List[Queue] = []
        self.skipped_singles2: List[Queue] = []
        self.skipped_charlie: List[Queue] = []
        self.skipped_statico: List[Queue] = []

        # Dizionario per memorizzare i nomi dei giocatori
        self.player_names: Dict[str, str] = {}

        # Inizializza le code con i nuovi formati ID
        # for i in range(1, 11):
        #     couple_id = f"GIALLO-{i:02d}"
        #     single_id = f"BLU-{i:02d}"
        #     charlie_id = f"VERDE-{i:02d}"
            
        #     self.add_couple(couple_id)
        #     self.add_single(single_id)
        #     self.add_charlie_player(charlie_id)

        self.player_start_times: Dict[str, datetime.datetime] = {}
        self.player_durations: Dict[str, float] = {}

    def add_couple(self, couple_id, name) -> None:
        self.queue_couples.append({'id': couple_id, 'arrival': self.get_current_time()})
        self.player_names[couple_id] = name

    def add_single(self, single_id, name) -> None:
        self.queue_singles.append({'id': single_id, 'arrival': self.get_current_time()})
        self.player_names[single_id] = name

    def add_couple2(self, couple_id, name) -> None:
        self.queue_couples2.append({'id': couple_id, 'arrival': self.get_current_time()})
        self.player_names[couple_id] = name

    def add_single2(self, single_id, name) -> None:
        self.queue_singles2.append({'id': single_id, 'arrival': self.get_current_time()})
        self.player_names[single_id] = name 

    def add_charlie_player(self, player_id, name) -> None:
        """Aggiunge un giocatore alla coda Charlie"""
        if not any(p['id'] == player_id for p in self.queue_charlie):
            self.queue_charlie.append({
                'id': player_id,
                'arrival': self.get_current_time(),
                'name': name
            })
            self.player_names[player_id] = name
            if not self.next_player_charlie_id and not self.next_player_charlie_locked:
                self.next_player_charlie_id = player_id
                self.next_player_charlie_name = name
                self.next_player_charlie_locked = True

    def add_statico_player(self, player_id: str, name: str) -> None:
        """Aggiunge un giocatore alla coda Statico"""
        if not any(p['id'] == player_id for p in self.queue_statico):
            self.queue_statico.append({
                'id': player_id,
                'arrival': self.get_current_time(),
                'name': name
            })
            self.player_names[player_id] = name
            if not self.next_player_statico_id and not self.next_player_statico_locked:
                self.next_player_statico_id = player_id
                self.next_player_statico_name = name
                self.next_player_statico_locked = True

    def record_couple_game(self, timer_duration: float, official_score: float) -> None:
        """
        Registra i tempi (in minuti) relativi a un game coppia:
        - timer_duration: durata effettiva del timer (usata per medie)
        - official_score: punteggio ufficiale (timer + penalità, per classifica)
        """
        # Aggiungi alla storia dei timer per le medie
        self.couple_timer_history.append(timer_duration)
        # Aggiungi lo score ufficiale alla storia per la classifica (o DB)
        self.couple_history_total.append((self.current_player_couple['id'], official_score))  # Store player_id with score

        # >>> IL RESTO DELLA LOGICA RIMANE QUASI INVARIATO <<<
        # Mantiene la pista BRAVO occupata fino alla fine del game di coppia (questo è corretto)
        # self.current_player_bravo = None # Questo va gestito DOPO la chiamata a questa funzione, nello stop effettivo
        # self.couple_in_alfa = False     # Questo è gestito da button_third_pressed
        # self.couple_in_bravo = False    # Questo va gestito DOPO la chiamata a questa funzione

        # Memorizza la durata *ufficiale* nel dizionario per riferimento (se serve)
        player_id = self.current_player_couple['id'] if self.current_player_couple else None
        if player_id:
            self.player_durations[player_id] = official_score # Memorizza lo score ufficiale
            # Rimuovi start time se non serve più
            self.player_start_times.pop(player_id, None)

        # Aggiorna le medie (ora useranno le nuove liste timer)
        self.update_averages()
        # Aggiorna il prossimo giocatore
        self.update_next_player()

        # Resetta current_player_couple ALLA FINE
        self.current_player_couple = None
        self.current_player_bravo = None # Assicurati che bravo sia liberato qui
        self.couple_in_bravo = False     # Aggiorna stato bravo
        self.third_button_pressed = False # Resetta flag metà percorso


    def record_single_game(self, timer_duration: float, official_score: float) -> None:
        """
        Registra i tempi (in minuti) relativi a un game singolo:
          - timer_duration: durata effettiva del timer (usata per medie)
          - official_score: punteggio ufficiale (timer + penalità, per classifica)
        """
        player_id_stopped = None
        current_player_copy = None # Copia per logging dopo reset

        if self.current_player_alfa and self.current_player_alfa.get('id','').startswith("BLU"): # Controllo aggiunto per sicurezza
            player_id_stopped = self.current_player_alfa['id']
            current_player_copy = self.current_player_alfa.copy() # Copia prima di cancellare
            logging.info(f"[Record Single] Start processing for {player_id_stopped}. Timer={timer_duration:.4f}, Score={official_score:.4f}")

            # Aggiungi alle storie
            self.single_timer_history.append(timer_duration)
            self.single_history.append((player_id_stopped, official_score))  # Store player_id with score

            # Memorizza score ufficiale
            self.player_durations[player_id_stopped] = official_score
            self.player_start_times.pop(player_id_stopped, None)

            # Aggiorna medie (deve avvenire PRIMA di resettare il player se update_next_player dipende dallo stato attuale?)
            # Spostiamo update_averages dopo il reset per coerenza con gli altri record_ methods
            # self.update_averages() # <--- SPOSTATO SOTTO

            # ===> RESET STATO GIOCATORE E PISTA <===
            logging.debug(f"[Record Single] Resetting current_player_alfa (was {current_player_copy})")
            self.current_player_alfa = None
            self.single_in_alfa = False
            logging.debug(f"[Record Single] current_player_alfa is now {self.current_player_alfa}, single_in_alfa is {self.single_in_alfa}")

            # Aggiorna medie DOPO aver registrato i tempi ma PRIMA di scegliere il prossimo
            self.update_averages()
            logging.debug(f"[Record Single] Averages updated.")

            # Aggiorna il prossimo giocatore ORA che ALFA è libera
            self.update_next_player()
            logging.info(f"[Record Single] Processing finished for {player_id_stopped}. Next player updated.")

        else:
             current_id = self.current_player_alfa.get("id", "None") if self.current_player_alfa else "None"
             logging.warning(f"[Record Single] Called but no active Single player (BLU) found in ALFA. Current: {current_id}")


    def record_couple2_game(self, timer_duration: float, official_score: float) -> None:
        """
        Registra i tempi per un game coppia 2 (Rosa):
        - timer_duration: durata effettiva del timer (usata per medie T_total, T_mid2)
        - official_score: punteggio ufficiale (timer + penalità, per classifica)
        """
        if self.current_player_couple2:
            player_id = self.current_player_couple2['id']

            # Aggiungi timer_duration alla storia COMUNE dei timer coppia per medie
            self.couple_timer_history.append(timer_duration)
            # Aggiungi mid_time alla storia specifica di mid2 (se T_mid2 deve basarsi su questo)
            # Nota: mid_time ora deve essere calcolato e passato separatamente se serve ancora per T_mid2
            # self.couple_history_mid2.append(mid_time) # Dovrai passare mid_time a questa funzione se vuoi ancora T_mid2 separata

            # Aggiungi official_score alla storia COMUNE degli score per classifica
            self.couple_history_total.append((player_id, official_score))  # Store player_id with score

            # Memorizza lo score ufficiale del giocatore
            self.player_durations[player_id] = official_score
            self.player_start_times.pop(player_id, None)

            # Resetta lo stato per il set 2 (ALLA FINE)
            # self.current_player_bravo2 = None # Gestito dopo
            # self.couple_in_bravo2 = False     # Gestito dopo
            # self.third_button_pressed2 = False # Gestito dopo

            self.update_averages() # Aggiorna le medie
            self.update_next_player2() # Aggiorna il prossimo giocatore per il set 2

            # Rimuovi current_player_couple2 e resetta stato ALLA FINE
            self.current_player_couple2 = None
            self.current_player_bravo2 = None
            self.couple_in_bravo2 = False
            self.third_button_pressed2 = False


    def record_single2_game(self, timer_duration: float, official_score: float) -> None:
        """
        Registra i tempi per un game singolo 2 (Arancio):
        - timer_duration: durata effettiva del timer (usata per medie)
        - official_score: punteggio ufficiale (timer + penalità, per classifica)
        """
        if self.current_player_alfa2:
            player_id = self.current_player_alfa2['id']

            # Aggiungi timer_duration alla storia COMUNE dei timer singoli per medie
            self.single_timer_history.append(timer_duration)
            # Aggiungi official_score alla storia COMUNE degli score per classifica
            self.single_history2.append((player_id, official_score))  # Store player_id with score

            # Memorizza lo score ufficiale del giocatore
            self.player_durations[player_id] = official_score
            self.player_start_times.pop(player_id, None)

            # IMPORTANTE: Resetta lo stato PRIMA di chiamare update_next_player2()
            # in modo che rilevi correttamente che ALFA2 è libera
            self.current_player_alfa2 = None
            self.single_in_alfa2 = False

            # Aggiorna le medie e poi aggiorna il prossimo giocatore
            self.update_averages() # Aggiorna le medie
            
            # Ora che ALFA2 è libera ma BRAVO2 potrebbe essere ancora occupata,
            # update_next_player2() darà priorità ai singoli se ci sono
            self.update_next_player2() # Aggiorna il prossimo giocatore per il set 2

    def check_qualification(self, score_minutes: float, player_type: str) -> Tuple[bool, Optional[str]]:
        """
        Controlla se un punteggio si qualifica (migliore del giorno o top 3).
        Query diretta al DB 'scoring'.
        """
        # Necessario importare o avere accesso a:
        import sqlite3
        import logging
        # Assumendo che SQLITE_DB_PATH e sqlite_lock siano accessibili (es. globali in app.py)
        # o passati come argomenti se preferisci.

        is_qualified = False
        reason = None

        sqlite_lock = Lock()
        SQLITE_DB_PATH = 'stand_db.db'  # Database local MySQLite in cui salveremo le queue

        # Assicurati che SQLITE_DB_PATH sia definito correttamente dove questa funzione viene chiamata (app.py)
        # Assicurati che sqlite_lock sia definito correttamente dove questa funzione viene chiamata (app.py)
        db_path = SQLITE_DB_PATH
        lock = sqlite_lock

        today_str = self.get_current_time().strftime('%Y-%m-%d')
        logging.debug(f"[QUAL CHECK] Checking score {score_minutes} for type {player_type} against date {today_str}")

        try:
            with lock: # Usa il lock definito in app.py
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 1. Migliore del Giorno
                cursor.execute("""
                    SELECT MIN(score) FROM scoring
                    WHERE player_type = ? AND date(created_at, 'localtime') = ?
                """, (player_type, today_str))
                result = cursor.fetchone()
                best_today_score_db = result[0] if result and result[0] is not None else None
                best_today_score = float(best_today_score_db) if best_today_score_db is not None else float('inf')
                logging.debug(f"[QUAL CHECK] Best today score in DB: {best_today_score_db} -> {best_today_score}")


                # Usa una tolleranza molto piccola per confronti float se necessario
                # epsilon = 1e-9
                # if score_minutes <= best_today_score + epsilon:
                if score_minutes <= best_today_score:
                    is_qualified = True
                    reason = 'best_today'
                    logging.debug(f"[QUAL CHECK] Qualifies as best_today.")

                # 2. Top 3 Generale
                cursor.execute("""
                    SELECT score FROM scoring
                    WHERE player_type = ?
                    ORDER BY score ASC
                    LIMIT 3
                """, (player_type,))
                top_scores_result = cursor.fetchall()
                top_scores = [float(row[0]) for row in top_scores_result if row[0] is not None]
                logging.debug(f"[QUAL CHECK] Top 3 scores in DB: {top_scores}")

                conn.close() # Chiudi connessione prima di elaborare i top scores

            qualifies_top_3 = False
            if len(top_scores) < 3:
                qualifies_top_3 = True # Si qualifica se ci sono meno di 3 punteggi
                logging.debug(f"[QUAL CHECK] Qualifies top_3 (less than 3 scores exist).")
            # elif score_minutes <= top_scores[-1] + epsilon: # Confronta con il terzo (ultimo della lista)
            elif score_minutes <= top_scores[-1]:
                 qualifies_top_3 = True
                 logging.debug(f"[QUAL CHECK] Qualifies top_3 (score <= {top_scores[-1]}).")


            if qualifies_top_3:
                 is_qualified = True
                 if reason is None: # Imposta solo se non è già 'best_today'
                      reason = 'top_3_overall'

        except Exception as e:
            logging.error(f"[QUAL CHECK] Error checking qualification for {player_type} score {score_minutes}: {e}", exc_info=True)
            return False, None # Errore durante il check

        logging.debug(f"[QUAL CHECK] Final result: Qualified={is_qualified}, Reason={reason}")
        return is_qualified, reason            

    def record_charlie_game(self, timer_duration: float) -> None:
        """
        Registra la DURATA DEL TIMER (in minuti) per un game charlie.
        Questo tempo viene usato SOLO per calcolare la media T_charlie per le stime.
        Libera la pista Charlie e aggiorna le medie.
        """
        player_id_stopped = None
        if self.current_player_charlie:
            player_id_stopped = self.current_player_charlie.get('id')
            logging.info(f"[CHARLIE TIMER RECORD] Player {player_id_stopped} stopped. Timer duration: {timer_duration:.4f} minutes.")

            # Aggiungi la durata del timer alla NUOVA history specifica
            self.charlie_timer_history.append(timer_duration)

            # Pulisci lo stato del giocatore corrente e della pista
            self.current_player_charlie = None
            self.player_in_charlie = False

            # Rimuovi il tempo di inizio (opzionale, ma buona pulizia)
            if player_id_stopped in self.player_start_times:
                del self.player_start_times[player_id_stopped]
            # Potresti voler rimuovere anche da self.player_durations se non più necessario dopo lo stop
            if player_id_stopped in self.player_durations:
                del self.player_durations[player_id_stopped]

            # Aggiorna le medie (che ora useranno charlie_timer_history per T_charlie)
            self.update_averages()

            # Aggiorna il prossimo giocatore per Charlie
            self.update_next_charlie_player() # Potrebbe essere necessario creare questa funzione o integrare la logica qui/in update_next_player
        else:
            logging.warning("[CHARLIE TIMER RECORD] Called record_charlie_game but no player was active.")

    def update_next_charlie_player(self):
        if self.queue_charlie:
            self.next_player_charlie_id = self.queue_charlie[0]['id']
            self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
            self.next_player_charlie_locked = True
        else:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False

    

    def format_time(self, time_in_minutes: float) -> str:
        """Formatta il tempo in minuti e secondi"""
        minutes = int(time_in_minutes)
        seconds = int((time_in_minutes - minutes) * 60)
        return f"{minutes}m {seconds}s"
    
    def get_leaderboard(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Restituisce la classifica basata sulle liste _history.
        Per Charlie, ora usa i punteggi ufficiali (manuali) salvati in chalie_history.
        """
        # Assicurati che i player_id/nomi siano corretti se non usi "COMPLETATO-..."
        # Potresti voler recuperare i nomi reali dalla tabella scoring se necessario.
        # Questa implementazione semplice usa un ID generico.
        couple_scores = sorted(self.couple_history_total)
        single_scores = sorted(self.single_history)
        charlie_scores = sorted(self.charlie_history) # <-- Legge i tempi UFFICIALI
        statico_scores = sorted(self.statico_history)

        # Funzione helper per formattare l'output della leaderboard
        def format_leaderboard(scores: List[float], prefix: str) -> List[Tuple[str, str]]:
            board = []
            # Recupera i dati dalla tabella scoring per avere ID/Nomi reali
            # Questo è un esempio SEMPLIFICATO. Per una leaderboard reale,
            # dovresti fare una query su 'scoring', ordinare per 'score'
            # e prendere i primi N, mostrando 'player_name' o 'player_id'.
            # Qui usiamo solo i valori numerici dalla history list.
            for i, time in enumerate(scores):
                # Per ora usiamo un ID generico basato sull'indice
                player_display_id = f"{prefix}-{i+1}"
                board.append((player_display_id, self.format_time(time)))
            return board

        # Query effettiva per la leaderboard (esempio per Charlie)
        def get_real_leaderboard(player_type: str, limit: int = 10) -> List[Tuple[str, str]]:
            board = []
            SQLITE_DB_PATH = 'stand_db.db'
            sqlite_lock = Lock() # Assumendo sia definita globalmente in app.py
            try:
                with sqlite_lock:
                    conn = sqlite3.connect(SQLITE_DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT player_name, player_id, score FROM scoring
                        WHERE player_type = ?
                        ORDER BY score ASC
                        LIMIT ?
                    """, (player_type, limit))
                    rows = cursor.fetchall()
                    conn.close()
                for row in rows:
                    player_name, player_id, score_minutes = row
                    display_name = player_id if player_id else player_name
                    board.append((display_name, self.format_time(score_minutes)))
            except Exception as e:
                logging.error(f"Error fetching real leaderboard for {player_type}: {e}")
            return board

        return {
            # Usa la funzione reale per la leaderboard
            'couples': get_real_leaderboard('couple'),
            'singles': get_real_leaderboard('single'),
            'charlie': get_real_leaderboard('charlie'),
            'statico': get_real_leaderboard('statico')

            # 'couples': format_leaderboard(couple_scores, "COPPIA"), # Vecchio modo
            # 'singles': format_leaderboard(single_scores, "SINGOLO"),# Vecchio modo
            # 'charlie': format_leaderboard(charlie_scores, "CHARLIE"),# Vecchio modo
            # 'statico': format_leaderboard(statico_scores, "STATICO") # Vecchio modo
        }


    def get_current_time(self) -> datetime.datetime:
        """Restituisce l'ora corrente nel fuso orario di Roma"""
        return datetime.datetime.now(self.rome_tz)

    def localize_time(self, dt):
        """Assicura che un datetime abbia il fuso orario di Roma"""
        if dt.tzinfo is None:
            return self.rome_tz.localize(dt)
        return dt
    
    

    # Dentro la classe GameBackend in main.py

    def update_averages(self) -> None:
        """
        Aggiorna i tempi medi USANDO LE DURATE DEI TIMER per T_total e T_single.
        T_mid e T_mid2 continuano a usare le loro storie specifiche (tempo fino al 3° pulsante).
        """
        min_games_for_avg = 5 # Numero minimo di game per calcolare la media
        logging.debug("Updating averages...")
        print(len(self.couple_history_mid))
        # Media T_mid (Set 1) - Basata sul tempo fino al pulsante 3 (da couple_history_mid)
        if len(self.couple_history_mid) >= min_games_for_avg:

            self.T_mid = sum(self.couple_history_mid) / len(self.couple_history_mid)
            logging.debug(f"Calculated T_mid from {len(self.couple_history_mid)} records: {self.T_mid:.4f}")
        else:
            self.T_mid = self.default_T_mid
            logging.debug(f"Using default T_mid: {self.T_mid:.4f} (records: {len(self.couple_history_mid)})")

        # Media T_mid2 (Set 2) - Basata sul tempo fino al pulsante 3 (da couple_history_mid2)
        if len(self.couple_history_mid2) >= min_games_for_avg:
            self.T_mid2 = sum(self.couple_history_mid2) / len(self.couple_history_mid2)
            logging.debug(f"Calculated T_mid2 from {len(self.couple_history_mid2)} records: {self.T_mid2:.4f}")
        else:
            # Potrebbe usare default_T_mid o un default specifico se definito
            self.T_mid2 = self.default_T_mid
            logging.debug(f"Using default T_mid2: {self.T_mid2:.4f} (records: {len(self.couple_history_mid2)})")

        # Media T_total (Coppie Combinate) - MODIFICATA: Usa la storia dei TIMER (couple_timer_history)
        if len(self.couple_timer_history) >= min_games_for_avg:
            self.T_total = sum(self.couple_timer_history) / len(self.couple_timer_history)
            logging.debug(f"Calculated T_total from {len(self.couple_timer_history)} TIMER records: {self.T_total:.4f}")
        else:
            self.T_total = self.default_T_total
            logging.debug(f"Using default T_total: {self.T_total:.4f} (timer records: {len(self.couple_timer_history)})")

        # Media T_single (Singoli Combinati) - MODIFICATA: Usa la storia dei TIMER (single_timer_history)
        if len(self.single_timer_history) >= min_games_for_avg:
            self.T_single = sum(self.single_timer_history) / len(self.single_timer_history)
            logging.debug(f"Calculated T_single from {len(self.single_timer_history)} TIMER records: {self.T_single:.4f}")
        else:
            self.T_single = self.default_T_single
            logging.debug(f"Using default T_single: {self.T_single:.4f} (timer records: {len(self.single_timer_history)})")

        # Media T_charlie - Basata sui timer registrati per Charlie (charlie_timer_history) - INVARIATA
        if len(self.charlie_timer_history) >= min_games_for_avg:
            self.T_charlie = sum(self.charlie_timer_history) / len(self.charlie_timer_history)
            logging.debug(f"Calculated T_charlie from {len(self.charlie_timer_history)} timer records: {self.T_charlie:.4f}")
        else:
            self.T_charlie = self.default_T_charlie
            logging.debug(f"Using default T_charlie: {self.T_charlie:.4f} (timer records: {len(self.charlie_timer_history)})")

        # Media T_statico - Basata sui tempi registrati per Statico (statico_history)
        if len(self.statico_history) >= min_games_for_avg:
            statico_times = [time for _, time in self.statico_history]  # Extract only the game_time values
            self.T_statico = sum(statico_times) / len(statico_times)
            logging.debug(f"Calculated T_statico from {len(statico_times)} records: {self.T_statico:.4f}")
        else:
            self.T_statico = self.default_T_statico
            logging.debug(f"Using default T_statico: {self.T_statico:.4f} (records: {len(self.statico_history)})")

        logging.info(f"Averages Updated: T_mid={self.T_mid:.2f}, T_total(timer)={self.T_total:.2f}, T_single(timer)={self.T_single:.2f}, T_mid2={self.T_mid2:.2f}, T_charlie={self.T_charlie:.2f}, T_statico={self.T_statico:.2f}")
    def get_player_name(self, player_id: Optional[str]) -> str:
        if player_id is None:
            return "N/D"
        return self.player_names.get(player_id, player_id)

    def update_next_player(self) -> None:
        """
        Aggiorna next_player_alfa_bravo_id e next_player_alfa_bravo_name in base alla disponibilità in coda,
        considerando l'orario di entrata (campo 'arrival') oppure la priorità,
        in modo che il prossimo giocatore da entrare venga mostrato nella finestra "Prossimo ingresso".

        MODIFICATO: Priorità a Coppia (GIALLO) quando ALFA è occupata o entrambe sono occupate da una coppia.
        """
        logging.debug(f"[UpdateNextPlayer1] Start Check. Alfa: {self.current_player_alfa is not None}, Bravo: {self.current_player_bravo is not None}")

        next_id = None
        next_name = None
        locked = False

        if self.current_player_alfa is None and self.current_player_bravo is None:
            # Entrambe libere: Priorità Coppia (GIALLO)
            logging.debug("[UpdateNextPlayer1] Case: Both Free.")
            if self.queue_couples:
                next_id = self.queue_couples[0]['id']
                locked = True
            elif self.queue_singles:
                next_id = self.queue_singles[0]['id']
                locked = True

        elif self.current_player_alfa is None and self.current_player_bravo is not None:
            # ALFA libera, BRAVO occupato (Coppia sta finendo): Priorità Singolo (BLU) perché è l'unico che può entrare
            logging.debug("[UpdateNextPlayer1] Case: Alfa Free, Bravo Occupied.")
            if self.queue_singles:
                next_id = self.queue_singles[0]['id']
                locked = True
            # Mostra la prossima coppia in attesa, anche se non può entrare subito?
            # elif self.queue_couples:
            #     next_id = self.queue_couples[0]['id']
            #     locked = True # O False? Decidi se bloccare o meno

        # --- MODIFICA QUI ---
        # elif self.current_player_alfa is not None and self.current_player_bravo is None:
        # else: # Entrambe occupate (coppia appena partita)
        elif self.current_player_alfa is not None: # Se ALFA è occupata (da singolo O da coppia appena partita)
            # ALFA occupata (da Singolo o Coppia): Priorità Coppia (GIALLO), perché Bravo è libero o si libererà prima per una coppia.
            # Questo copre sia il caso (Alfa Occupata, Bravo Libero) sia (Alfa Occupata, Bravo Occupato)
            logging.debug("[UpdateNextPlayer1] Case: Alfa Occupied (Bravo Free or Occupied).")
            if self.queue_couples:
                next_id = self.queue_couples[0]['id']
                locked = True
            elif self.queue_singles:
                # Se non ci sono coppie, suggerisci il prossimo singolo che entrerà quando ALFA si libera
                next_id = self.queue_singles[0]['id']
                locked = True
        # --- FINE MODIFICA ---

        # Se non è stato trovato nessun giocatore in base allo stato delle piste,
        # ma ci sono giocatori in coda, mostra il primo disponibile in assoluto (fallback)
        if next_id is None:
            logging.debug("[UpdateNextPlayer1] Case: Fallback (no specific priority met, checking queues).")
            if self.queue_couples:
                next_id = self.queue_couples[0]['id']
                locked = True
            elif self.queue_singles:
                next_id = self.queue_singles[0]['id']
                locked = True

        # Aggiorna le variabili di stato
        if next_id:
            next_name = self.get_player_name(next_id)
            logging.debug(f"[UpdateNextPlayer1] Result: Next={next_id} ({next_name}), Locked={locked}")
        else:
            logging.debug("[UpdateNextPlayer1] Result: No next player found in queues.")
            next_name = None
            locked = False

        self.next_player_alfa_bravo_id = next_id
        self.next_player_alfa_bravo_name = next_name
        self.next_player_alfa_bravo_locked = locked

    def update_next_player2(self) -> None:
        """
        Aggiorna next_player_alfa_bravo_id2 e next_player_alfa_bravo_name2 in base alla disponibilità in coda,
        considerando solo coppie "ROSA" e singoli "ARANCIO" (o "BIANCO").
        
        Funziona esattamente come per la coda combined1:
        - Se entrambe le piste sono libere: priorità a coppia (ROSA)
        - Se ALFA2 è libera e BRAVO2 è occupata: priorità a singolo (ARANCIO/BIANCO) perché può entrare subito
        - Se ALFA2 è occupata (indipendentemente da BRAVO2): priorità a coppia (ROSA)
        """
        # Logga lo stato iniziale per debug
        logging.debug(f"[UpdateNextPlayer2] Start Check. Alfa2 Occupied: {self.current_player_alfa2 is not None}, Bravo2 Occupied: {self.current_player_bravo2 is not None}")
        next_id = None
        next_name = None
        locked = False

        # Caso 1: Entrambe le piste libere
        if self.current_player_alfa2 is None and self.current_player_bravo2 is None:
            # Priorità a Coppia (ROSA) se disponibile
            logging.debug("[UpdateNextPlayer2] Case: Both Free.")
            if self.queue_couples2:
                next_id = self.queue_couples2[0]['id']
                locked = True
            # Altrimenti, il prossimo Singolo (ARANCIO/BIANCO)
            elif self.queue_singles2:
                next_id = self.queue_singles2[0]['id']
                locked = True

        # Caso 2: ALFA2 libera, BRAVO2 occupato (Coppia ROSA sta finendo)
        elif self.current_player_alfa2 is None and self.current_player_bravo2 is not None:
            # Solo un Singolo (ARANCIO/BIANCO) può entrare ora in ALFA2
            logging.debug("[UpdateNextPlayer2] Case: Alfa2 Free, Bravo2 Occupied. Priority to singles (ARANCIO/BIANCO).")
            if self.queue_singles2:
                next_id = self.queue_singles2[0]['id']
                locked = True
            # Potresti anche mostrare la prossima coppia come "in attesa" ma non bloccata
            elif self.queue_couples2:
                next_id = self.queue_couples2[0]['id']
                locked = False # Non bloccare perché non può entrare subito

        # Caso 3: ALFA2 è occupata (non importa lo stato di BRAVO2)
        elif self.current_player_alfa2 is not None:
            # Se ALFA2 è occupata (da un Singolo o da una Coppia appena partita),
            # la priorità per il *prossimo* slot va alla Coppia (ROSA),
            # perché è quella che può utilizzare BRAVO2 non appena si libera.
            logging.debug("[UpdateNextPlayer2] Case: Alfa2 Occupied (Bravo2 state irrelevant for *next* priority). Priority to couples (ROSA).")
            if self.queue_couples2:
                next_id = self.queue_couples2[0]['id']
                locked = True
            # Solo se non ci sono coppie in attesa, suggerisci il prossimo singolo
            elif self.queue_singles2:
                next_id = self.queue_singles2[0]['id']
                locked = True
        
        # Fallback: Se nessun caso ha trovato un ID, ma le code non sono vuote
        if next_id is None:
             logging.debug("[UpdateNextPlayer2] Case: Fallback (no specific priority met, checking queues).")
             if self.queue_couples2:
                 next_id = self.queue_couples2[0]['id']
                 locked = True
             elif self.queue_singles2:
                 next_id = self.queue_singles2[0]['id']
                 locked = True

        # Aggiorna le variabili di stato del backend
        if next_id:
            next_name = self.get_player_name(next_id)
            logging.debug(f"[UpdateNextPlayer2] Result: Next={next_id} ({next_name}), Locked={locked}")
        else:
            logging.debug("[UpdateNextPlayer2] Result: No next player found in queues.")
            next_name = None
            locked = False

        self.next_player_alfa_bravo_id2 = next_id
        self.next_player_alfa_bravo_name2 = next_name
        self.next_player_alfa_bravo_locked2 = locked
                          

    def start_game(self, is_couple: bool) -> None:
        now = self.get_current_time()
        if is_couple:
            if self.queue_couples:
                self.current_player_couple = self.queue_couples.pop(0)
                self.ALFA_next_available = now + datetime.timedelta(minutes=self.T_mid)
                self.BRAVO_next_available = now + datetime.timedelta(minutes=self.T_total)
                self.current_player_alfa = self.current_player_couple
                self.current_player_bravo = self.current_player_couple
                self.couple_in_alfa = True
                self.couple_in_bravo = True
                self.player_start_times[self.current_player_couple['id']] = now
                if self.queue_singles:
                    self.next_player_alfa_bravo_id = self.queue_singles[0]['id']
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                    self.next_player_alfa_bravo_locked = True
                else:
                    self.next_player_alfa_bravo_id = self.queue_couples[0]['id'] if self.queue_couples else None
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id) if self.next_player_alfa_bravo_id else None
                    self.next_player_alfa_bravo_locked = True if self.next_player_alfa_bravo_id else False
            else:
                raise ValueError("No couples in queue to start the game.")
        else:
            if self.queue_singles:
                self.current_player_alfa = self.queue_singles.pop(0)
                self.single_in_alfa = True
                self.ALFA_next_available = now + datetime.timedelta(minutes=self.T_single)
                self.player_start_times[self.current_player_alfa['id']] = now
                if self.queue_couples:
                    self.next_player_alfa_bravo_id = self.queue_couples[0]['id']
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                    self.next_player_alfa_bravo_locked = True
                else:
                    self.next_player_alfa_bravo_id = self.queue_singles[0]['id'] if self.queue_singles else None
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id) if self.next_player_alfa_bravo_id else None
                    self.next_player_alfa_bravo_locked = True if self.next_player_alfa_bravo_id else False
            else:
                raise ValueError("No singles in queue to start the game.")
            
    def start_game2(self, is_couple: bool) -> None:
        now = self.get_current_time()
        if is_couple:
            if self.queue_couples2:
                self.current_player_couple2 = self.queue_couples2.pop(0)
                self.ALFA_next_available2 = now + datetime.timedelta(minutes=self.T_mid)   
                self.BRAVO_next_available2 = now + datetime.timedelta(minutes=self.T_total)
                self.current_player_alfa2 = self.current_player_couple2
                self.current_player_bravo2 = self.current_player_couple2
                self.couple_in_alfa2 = True
                self.couple_in_bravo2 = True
                self.player_start_times[self.current_player_couple2['id']] = now    
                if self.queue_singles2:
                    self.next_player_alfa_bravo_id2 = self.queue_singles2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                else:   
                    self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id'] if self.queue_couples2 else None
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2) if self.next_player_alfa_bravo_id2 else None
                    self.next_player_alfa_bravo_locked2 = True if self.next_player_alfa_bravo_id2 else False
            else:
                raise ValueError("No couples in queue to start the game.")
        else:   
            if self.queue_singles2:
                self.current_player_alfa2 = self.queue_singles2.pop(0)
                self.single_in_alfa2 = True
                self.ALFA_next_available2 = now + datetime.timedelta(minutes=self.T_single)
                self.player_start_times[self.current_player_alfa2['id']] = now
                if self.queue_couples2:
                    self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                else:
                    self.next_player_alfa_bravo_id2 = self.queue_singles2[0]['id'] if self.queue_singles2 else None
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2) if self.next_player_alfa_bravo_id2 else None
                    self.next_player_alfa_bravo_locked2 = True if self.next_player_alfa_bravo_id2 else False
            else:
                raise ValueError("No singles in queue to start the game.")  
                

    def start_statico_game(self, pista: str) -> None:
        """Avvia un gioco sulla pista Statico specificata"""
        if not self.queue_statico:
            raise ValueError("Nessun giocatore in coda per Statico")
        
        if pista == 'delta' and not self.current_player_delta:
            self.current_player_delta = {
                'id': self.queue_statico[0]['id'],
                'arrival': self.get_current_time()
            }
            self.DELTA_next_available = self.get_current_time() + datetime.timedelta(minutes=self.T_statico)
            self.player_start_times[self.current_player_delta['id']] = self.get_current_time()
            # Rimuovi il giocatore dalla coda
            self.queue_statico.pop(0)
            
        elif pista == 'echo' and not self.current_player_echo:
            self.current_player_echo = {
                'id': self.queue_statico[0]['id'],
                'arrival': self.get_current_time()
            }
            self.ECHO_next_available = self.get_current_time() + datetime.timedelta(minutes=self.T_statico)
            self.player_start_times[self.current_player_echo['id']] = self.get_current_time()
            # Rimuovi il giocatore dalla coda
            self.queue_statico.pop(0)
        
        # Aggiorna il prossimo giocatore
        if self.queue_statico:
            self.next_player_statico_id = self.queue_statico[0]['id']
            self.next_player_statico_name = self.get_player_name(self.next_player_statico_id)
            self.next_player_statico_locked = True
        else:
            self.next_player_statico_id = None
            self.next_player_statico_name = None
            self.next_player_statico_locked = False

    def record_statico_game(self, game_time: float, pista: str) -> None:
        """Registra il tempo di gioco per la pista Statico specificata"""
        if pista == 'delta' and self.current_player_delta:
            player_id = self.current_player_delta['id']
            self.statico_history.append((player_id, game_time))  # Store player_id with score
            self.update_averages()
            self.player_start_times.pop(player_id, None)
            self.current_player_delta = None
            
        elif pista == 'echo' and self.current_player_echo:
            player_id = self.current_player_echo['id']
            self.statico_history.append((player_id, game_time))  # Store player_id with score
            self.update_averages()
            self.player_start_times.pop(player_id, None)
            self.current_player_echo = None

    def simulate_schedule(self) -> Dict[str, datetime.datetime]:
        now = self.get_current_time()
        estimated_times = {}
        
        # Calcolo lunghezze code
        len_giallo = len(self.queue_couples)
        len_blu = len(self.queue_singles)
        
        # Per ogni giocatore blu (singles)
        for current_blu, player in enumerate(self.queue_singles, 1):
            # Calcola il tempo di attesa
            min_att = self.calculate_blue_waiting_time(
                current_blu=current_blu,
                len_giallo=len_giallo
            )
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        # Per ogni giocatore giallo (couples)
        for current_giallo, player in enumerate(self.queue_couples, 1):
            min_att = self.calculate_yellow_waiting_time(
                current_giallo=current_giallo,
                len_blu=len_blu,
                dt_total=self.T_total,
                dt_mid=self.T_mid,
                dt_single=self.T_single
            )
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        return estimated_times

    def simulate_schedule2(self) -> Dict[str, datetime.datetime]:
        now = self.get_current_time()
        sim_time = max(now, self.ALFA_next_available2)

        self.ALFA_next_available2 = self.localize_time(self.ALFA_next_available2)
        BRAVO_avail2 = self.BRAVO_next_available2 if self.BRAVO_next_available2 > sim_time else sim_time
        
        dt_mid2 = datetime.timedelta(minutes=self.T_mid)
        dt_total2 = datetime.timedelta(minutes=self.T_total)
        dt_single2 = datetime.timedelta(minutes=self.T_single)
        
        couples = deepcopy(self.queue_couples2)
        singles = deepcopy(self.queue_singles2) 

        estimated_times2 = {}

        while couples or singles:
            if not couples and singles:
                item = singles.pop(0)   
                start_time = sim_time
                estimated_times2[item['id']] = start_time
                sim_time = start_time + dt_single2
                continue
            
            if BRAVO_avail2 <= sim_time:
                if couples: 
                    item = couples.pop(0)
                    start_time = sim_time
                    estimated_times2[item['id']] = start_time
                    sim_time = start_time + dt_mid2
                    BRAVO_avail2 = start_time + dt_total2
                    continue
                else:
                    if singles:
                        item = singles.pop(0)
                        start_time = sim_time
                        estimated_times2[item['id']] = start_time
                        sim_time = start_time + dt_single2
                        continue
                    else:
                        break
            else:
                if singles:
                    item = singles.pop(0)
                    start_time = sim_time
                    estimated_times2[item['id']] = start_time
                    sim_time = start_time + dt_single2
                    continue    
                else:
                    sim_time = BRAVO_avail2
                    continue

        return estimated_times2
    

    def get_waiting_board(self) -> Tuple[
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]],
        List[Tuple[int, str, Union[datetime.datetime, str]]]  # Aggiungiamo la board statico
    ]:
        now = self.get_current_time()
        # Calcola i tempi stimati di ingresso
        est1 = self.simulate_schedule()
        est2 = self.simulate_schedule2()
        # --- Logica per next_player_alfa_bravo_id (usa est1) ---
        if not self.next_player_alfa_bravo_locked:
            # ... (logica esistente per next_player_alfa_bravo_id usando est1) ...
            # Caso speciale: se c'è una coppia in BRAVO e un singolo in ALFA, prioritizza le coppie
            if self.couple_in_bravo and self.single_in_alfa and self.queue_couples:
                self.next_player_alfa_bravo_id = self.queue_couples[0]['id']
                self.next_player_alfa_bravo_locked = True
            else:
                # Altrimenti, controlla il tempo stimato per ogni giocatore in coda
                next_player_found = False
                for queue_item in self.queue_couples + self.queue_singles:
                    estimated_time = est1.get(queue_item['id'])
                    if estimated_time:
                        minutes_to_entry = (estimated_time - now).total_seconds() / 60
                        # Imposta come prossimo se l'ingresso è imminente o è il primo della coda simulata
                        if minutes_to_entry <= 2 or not next_player_found:
                            self.next_player_alfa_bravo_id = queue_item['id']
                            self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id) # Aggiorna anche il nome
                            self.next_player_alfa_bravo_locked = True
                            next_player_found = True
                            # Se l'ingresso è imminente, blocca la scelta
                            if minutes_to_entry <= 2:
                                break # Esci dal ciclo una volta trovato un giocatore imminente


        # --- Logica per next_player_alfa_bravo_id2 (usa est2) --- (NUOVA)
        if not self.next_player_alfa_bravo_locked2:
            if self.couple_in_bravo2 and self.single_in_alfa2 and self.queue_couples2:
                self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2) # Aggiorna anche il nome
                self.next_player_alfa_bravo_locked2 = True
            else:
                next_player_found2 = False
                for queue_item in self.queue_couples2 + self.queue_singles2:
                    estimated_time = est2.get(queue_item['id']) # Usa est2
                    if estimated_time:
                        minutes_to_entry = (estimated_time - now).total_seconds() / 60
                        if minutes_to_entry <= 2 or not next_player_found2:
                            self.next_player_alfa_bravo_id2 = queue_item['id']
                            self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2) # Aggiorna anche il nome
                            self.next_player_alfa_bravo_locked2 = True
                            next_player_found2 = True
                            if minutes_to_entry <= 2:
                                break

            # --- Costruzione board ALFA/BRAVO 1 (usa est1) ---
        couples_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        for idx, item in enumerate(self.queue_couples):
            estimated = est1.get(item['id'], "N/D") # Default a "N/D" se non trovato
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id else estimated
            couples_board.append((idx + 1, item['id'], display_time))

        singles_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        for idx, item in enumerate(self.queue_singles):
            estimated = est1.get(item['id'], "N/D") # Default a "N/D"
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id else estimated
            singles_board.append((idx + 1, item['id'], display_time))

        # --- Costruzione board ALFA/BRAVO 2 (usa est2) --- (MODIFICATA)
        couples_board2: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        for idx, item in enumerate(self.queue_couples2):
            estimated = est2.get(item['id'], "N/D") # Usa est2, Default a "N/D"
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id2 else estimated
            couples_board2.append((idx + 1, item['id'], display_time))

        singles_board2: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        for idx, item in enumerate(self.queue_singles2):
            estimated = est2.get(item['id'], "N/D") # Usa est2, Default a "N/D"
            display_time = "PROSSIMO INGRESSO" if item['id'] == self.next_player_alfa_bravo_id2 else estimated
            singles_board2.append((idx + 1, item['id'], display_time))

            charlie_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
            for idx, item in enumerate(self.queue_charlie):
                if item['id'] == self.next_player_charlie_id:
                    charlie_board.append((idx + 1, item['id'], "PROSSIMO INGRESSO"))
                else:
                    players_ahead = idx
                    estimated_time = now + datetime.timedelta(minutes=self.T_charlie * players_ahead)
                    charlie_board.append((idx + 1, item['id'], estimated_time))

        # Costruzione della board statico (nuova)
        statico_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        for idx, item in enumerate(self.queue_statico):
            if item['id'] == self.next_player_statico_id:
                statico_board.append((idx + 1, item['id'], "PROSSIMO INGRESSO"))
            else:
                # Per statico usiamo una logica simile a Charlie
                players_ahead = idx
                # Consideriamo che ci sono 2 piste (DELTA e ECHO) quindi il tempo si dimezza
                estimated_time = now + datetime.timedelta(minutes=(self.T_statico * players_ahead) / 2)
                statico_board.append((idx + 1, item['id'], estimated_time))

            # Esempio ricalcolo Charlie
        charlie_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        charlie_sim_time = max(now, self.localize_time(self.CHARLIE_next_available))
        for idx, item in enumerate(self.queue_charlie):
            start_time = charlie_sim_time
            if item['id'] == self.next_player_charlie_id:
                display_time = "PROSSIMO INGRESSO"
            else:
                display_time = start_time

            charlie_board.append((idx + 1, item['id'], display_time))
            # Il prossimo può iniziare solo dopo che questo finisce
            charlie_sim_time = start_time + datetime.timedelta(minutes=self.T_charlie)


        # Esempio ricalcolo Statico
        statico_board: List[Tuple[int, str, Union[datetime.datetime, str]]] = []
        delta_avail = self.localize_time(self.DELTA_next_available)
        echo_avail = self.localize_time(self.ECHO_next_available)
        for idx, item in enumerate(self.queue_statico):
            # Trova la prossima pista disponibile da ora in poi
            next_avail_time = min(max(now, delta_avail), max(now, echo_avail))
            start_time = next_avail_time

            if item['id'] == self.next_player_statico_id:
                display_time = "PROSSIMO INGRESSO"
            else:
                display_time = start_time

            statico_board.append((idx + 1, item['id'], display_time))

            # Aggiorna la disponibilità della pista usata
            if max(now, delta_avail) <= max(now, echo_avail):
                delta_avail = start_time + datetime.timedelta(minutes=self.T_statico)
            else:
                echo_avail = start_time + datetime.timedelta(minutes=self.T_statico)
            

        return couples_board, singles_board, couples_board2, singles_board2, charlie_board, statico_board

    def button_third_pressed(self) -> None:
        """
        Gestisce la pressione del pulsante metà percorso (Coppia 1):
        - Libera la Pista ALFA se c'era una coppia GIALLO.
        - Calcola e registra la durata fino a questo punto in couple_history_mid.
        - Aggiorna lo stato e il prossimo giocatore.
        """
        now = self.get_current_time()
        logging.debug(f"[Button Third 1] Pressed at {now.isoformat()}")

        if self.current_player_alfa and self.current_player_alfa.get("id", "").startswith("GIALLO"):
            player_id = self.current_player_alfa['id']
            player_name = self.get_player_name(player_id) # Prendi il nome per log
            logging.info(f"[Button Third 1] Processing for couple: {player_id} ({player_name})")

            start_time = self.player_start_times.get(player_id)

            if start_time:
                # Calcola la durata fino a questo punto (tempo mid)
                mid_duration_minutes = (now - start_time).total_seconds() / 60.0
                logging.debug(f"[Button Third 1 {player_id}] Start time: {start_time.isoformat()}, Mid duration calculated: {mid_duration_minutes:.4f} min")

                # ===> Aggiungi alla storia MID 1 <===
                list_size_before = len(self.couple_history_mid)
                self.couple_history_mid.append(mid_duration_minutes)
                try:
                    sqlite_lock = Lock()
                    SQLITE_DB_PATH = 'stand_db.db'  # Database local MySQLite in cui salveremo le queue
                    with sqlite_lock:
                        conn = sqlite3.connect(SQLITE_DB_PATH)
                        cursor = conn.cursor()
                        # Inserisci il record specifico del timer
                        cursor.execute(
                            "INSERT INTO mid_times (couple_type, mid_duration_minutes) VALUES (?, ?)",
                            ("couple1", mid_duration_minutes)
                        )
                        conn.commit()
                        conn.close()
                    logging.info(f"[AVG TIME DB SAVE] Success for {player_id}.")
                except sqlite3.Error as db_err:
                    logging.error(f"[AVG TIME DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
                    # Potremmo decidere di continuare comunque o ritornare errore? Per ora continuiamo.
                except Exception as e:
                    logging.error(f"[AVG TIME DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
                    # Continuiamo
                list_size_after = len(self.couple_history_mid)
                logging.info(f"[Button Third 1 {player_id}] Appended mid_duration {mid_duration_minutes:.4f} to couple_history_mid. Size: {list_size_before} -> {list_size_after}")

                # Potresti voler aggiornare le medie subito dopo aver aggiunto un nuovo dato?
                # self.update_averages() # Valuta se chiamarlo qui o attendere la fine del gioco

            else:
                # Errore: start_time non trovato
                logging.error(f"[Button Third 1 {player_id}] CRITICAL: Start time not found! Cannot record mid_duration.")
                # Nonostante l'errore, liberiamo la pista per evitare blocchi, ma logghiamo l'errore.
                # Non aggiungiamo nulla a couple_history_mid in questo caso.

            # Procedi comunque a liberare la pista e aggiornare lo stato
            self.third_button_pressed = True # Flag per can_stop_couple
            self.couple_in_alfa = False     # Aggiorna stato pista
            logging.debug(f"[Button Third 1 {player_id}] Resetting current_player_alfa (was {self.current_player_alfa}) and setting third_button_pressed=True")
            self.current_player_alfa = None    # Libera la pista ALPHA
            # Aggiorna subito chi può entrare ora che ALFA è libera
            self.update_next_player()
            logging.info(f"[Button Third 1 {player_id}] Alfa track freed. Next player updated.")

        else:
            current_id = self.current_player_alfa.get("id", "None") if self.current_player_alfa else "None"
            logging.warning(f"[Button Third 1] Pressed but no Couple (GIALLO) found in ALFA. Current: {current_id}. Action ignored.")
            # Non sollevare eccezione qui, altrimenti blocca l'app se premuto per errore
            # raise ValueError(f"Pulsante metà percorso premuto ma non c'è una Coppia (GIALLO) in ALFA (attuale: {current_id}).")

    def button_third_pressed2(self) -> None:
        """
        Gestisce la pressione del pulsante metà percorso (Coppia 2):
        - Libera la Pista ALFA2 se c'era una coppia ROSA.
        - Calcola e registra la durata fino a questo punto in couple_history_mid2.
        - Aggiorna lo stato e il prossimo giocatore.
        """
        now = self.get_current_time()
        logging.debug(f"[Button Third 2] Pressed at {now.isoformat()}")

        # Usa startswith("ROSA") per identificare la coppia 2
        if self.current_player_alfa2 and self.current_player_alfa2.get("id", "").startswith("ROSA"):
            player_id = self.current_player_alfa2['id']
            player_name = self.get_player_name(player_id)
            logging.info(f"[Button Third 2] Processing for couple2: {player_id} ({player_name})")

            start_time = self.player_start_times.get(player_id)

            if start_time:
                # Calcola la durata fino a questo punto (tempo mid 2)
                mid2_duration_minutes = (now - start_time).total_seconds() / 60.0
                logging.debug(f"[Button Third 2 {player_id}] Start time: {start_time.isoformat()}, Mid2 duration calculated: {mid2_duration_minutes:.4f} min")

                # ===> Aggiungi alla storia MID 2 <===
                list_size_before = len(self.couple_history_mid2)
                self.couple_history_mid2.append(mid2_duration_minutes)
                try:
                    sqlite_lock = Lock()
                    SQLITE_DB_PATH = 'stand_db.db'  # Database local MySQLite in cui salveremo le queue
                    with sqlite_lock:
                        conn = sqlite3.connect(SQLITE_DB_PATH)
                        cursor = conn.cursor()
                        # Inserisci il record specifico del timer
                        cursor.execute(
                            "INSERT INTO mid_times (couple_type, mid_duration_minutes) VALUES (?, ?)",
                            ("couple2", mid2_duration_minutes)
                        )
                        conn.commit()
                        conn.close()
                    logging.info(f"[AVG TIME DB SAVE] Success for {player_id}.")
                except sqlite3.Error as db_err:
                    logging.error(f"[AVG TIME DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
                    # Potremmo decidere di continuare comunque o ritornare errore? Per ora continuiamo.
                except Exception as e:
                    logging.error(f"[AVG TIME DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
                    # Continuiamo
                list_size_after = len(self.couple_history_mid2)
                logging.info(f"[Button Third 2 {player_id}] Appended mid2_duration {mid2_duration_minutes:.4f} to couple_history_mid2. Size: {list_size_before} -> {list_size_after}")

                # self.update_averages() # Valuta se chiamarlo qui

            else:
                logging.error(f"[Button Third 2 {player_id}] CRITICAL: Start time not found! Cannot record mid2_duration.")
                # Libera comunque la pista

            # Libera pista e aggiorna stato
            self.third_button_pressed2 = True # Flag per can_stop_couple2
            self.couple_in_alfa2 = False
            # self.ALFA_next_available2 = now # Rende ALFA 2 disponibile ora? Potrebbe essere prematuro se deve aspettare Bravo2? Togliamolo per ora.
            logging.debug(f"[Button Third 2 {player_id}] Resetting current_player_alfa2 (was {self.current_player_alfa2}) and setting third_button_pressed2=True")
            self.current_player_alfa2 = None # Libera la pista ALFA 2
            # Aggiorna subito chi è il prossimo per Pista 2
            self.update_next_player2()
            logging.info(f"[Button Third 2 {player_id}] Alfa2 track freed. Next player 2 updated.")

        else:
            current_id = self.current_player_alfa2.get("id", "None") if self.current_player_alfa2 else "None"
            logging.warning(f"[Button Third 2] Pressed but no Couple2 (ROSA) found in ALFA2. Current: {current_id}. Action ignored.")
            # Non sollevare eccezione
            # raise ValueError(f"Pulsante metà percorso 2 premuto ma non c'è Coppia 2 (Rosa) in ALFA 2 (attuale: {current_id}).")

    def can_stop_couple(self) -> bool:
        "Verifica se una coppia può fermarsi"
        # Deve esserci una coppia in BRAVO e il pulsante 3 deve essere stato premuto

        can_stop = self.third_button_pressed and \
                   self.current_player_bravo is not None and \
                   self.current_player_bravo.get("id","").startswith("GIALLO") and \
                   self.current_player_couple is not None and \
                   self.current_player_couple.get("id","") == self.current_player_bravo.get("id","") # Assicurati che sia la stessa coppia


        return can_stop

    
    

    def can_stop_couple2(self) -> bool:
        can_stop = self.third_button_pressed2 and \
                   self.current_player_bravo2 is not None and \
                   self.current_player_bravo2.get("id", "").startswith("ROSA") and \
                   self.current_player_couple2 is not None and \
                   self.current_player_couple2.get("id","") == self.current_player_bravo2.get("id","")

        return can_stop

    def skip_player(self, player_id: str) -> None:
        """Sposta un giocatore nella lista degli skippati (Alfa/Bravo)"""
        player = next((c for c in self.queue_couples if c['id'] == player_id), None)
        if player:
            self.queue_couples.remove(player)
            self.skipped_couples.append(player)
            # Set the next player to the next couple in the queue
            if self.queue_couples:
                self.next_player_alfa_bravo_id = self.queue_couples[0]['id']
                self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                self.next_player_alfa_bravo_locked = True
            else:
                self.next_player_alfa_bravo_id = None
                self.next_player_alfa_bravo_name = None
                self.next_player_alfa_bravo_locked = False
        else:
            player = next((s for s in self.queue_singles if s['id'] == player_id), None)
            if player:
                self.queue_singles.remove(player)
                self.skipped_singles.append(player)
                # Set the next player to the next single in the queue
                if self.queue_singles:
                    self.next_player_alfa_bravo_id = self.queue_singles[0]['id']
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                    self.next_player_alfa_bravo_locked = True
                elif self.queue_couples:
                    self.next_player_alfa_bravo_id = self.queue_couples[0]['id']
                    self.next_player_alfa_bravo_name = self.get_player_name(self.next_player_alfa_bravo_id)
                    self.next_player_alfa_bravo_locked = True
                else:
                    self.next_player_alfa_bravo_id = None
                    self.next_player_alfa_bravo_name = None
                    self.next_player_alfa_bravo_locked = False

    def skip_player2(self, player_id: str) -> None:
        """Sposta un giocatore nella lista degli skippati (Alfa/Bravo)"""
        player = next((c for c in self.queue_couples2 if c['id'] == player_id), None)
        if player:
            self.queue_couples2.remove(player)
            self.skipped_couples2.append(player)    
            if self.queue_couples2:
                self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                self.next_player_alfa_bravo_locked2 = True
            else:
                self.next_player_alfa_bravo_id2 = None  
                self.next_player_alfa_bravo_name2 = None
                self.next_player_alfa_bravo_locked2= False 
        else:
            player = next((s for s in self.queue_singles2 if s['id'] == player_id), None)
            if player:
                self.queue_singles2.remove(player)
                self.skipped_singles2.append(player)    
                if self.queue_singles2:
                    self.next_player_alfa_bravo_id2 = self.queue_singles2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                elif self.queue_couples2:
                    self.next_player_alfa_bravo_id2 = self.queue_couples2[0]['id']
                    self.next_player_alfa_bravo_name2 = self.get_player_name(self.next_player_alfa_bravo_id2)
                    self.next_player_alfa_bravo_locked2 = True
                else:   
                    self.next_player_alfa_bravo_id2 = None
                    self.next_player_alfa_bravo_name2 = None
                    self.next_player_alfa_bravo_locked2 = False

    def skip_charlie_player(self, player_id: str) -> None:
        """Sposta un giocatore nella lista degli skippati (Charlie)"""
        player = next((p for p in self.queue_charlie if p['id'] == player_id), None)
        if player:
            self.queue_charlie.remove(player)
            self.skipped_charlie.append(player)
            # Set the next player to the next Charlie in the queue
            if self.queue_charlie:
                self.next_player_charlie_id = self.queue_charlie[0]['id']
                self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
                self.next_player_charlie_locked = True
            else:
                self.next_player_charlie_id = None
                self.next_player_charlie_name = None
                self.next_player_charlie_locked = False

    def skip_statico_player(self, player_id: str) -> None:
        """Sposta un giocatore nella lista degli skippati (Statico)"""
        player = next((p for p in self.queue_statico if p['id'] == player_id), None)
        if player:
            self.queue_statico.remove(player)
            self.skipped_statico.append(player)
            # Set the next player to the next Statico in the queue
            if self.queue_statico:
                self.next_player_statico_id = self.queue_statico[0]['id']
                self.next_player_statico_name = self.get_player_name(self.next_player_statico_id)
                self.next_player_statico_locked = True
            else:
                self.next_player_statico_id = None
                self.next_player_statico_name = None
                self.next_player_statico_locked = False            

    def restore_skipped(self, player_id: str) -> None:
        """Ripristina un giocatore skippato in coda come priorità"""
        player = next((c for c in self.skipped_couples if c['id'] == player_id), None)
        if player:
            self.skipped_couples.remove(player)
            self.queue_couples.insert(0, player)
        else:
            player = next((s for s in self.skipped_singles if s['id'] == player_id), None)
            if player:
                self.skipped_singles.remove(player)
                self.queue_singles.insert(0, player)
            else:
                player = next((p for p in self.skipped_charlie if p['id'] == player_id), None)
                if player:
                    self.skipped_charlie.remove(player)
                    self.queue_charlie.insert(0, player)
                

    def restore_skipped_as_next(self, player_id: str) -> None:
        """Ripristina un giocatore skippato come prossimo nella coda"""
        # Cerca in tutte le liste di skippati
        player = next((c for c in self.skipped_couples if c['id'] == player_id), None)
        if player:
            self.skipped_couples.remove(player)
            self.queue_couples.insert(0, player)
            self.next_player_alfa_bravo_id = player_id
            self.next_player_alfa_bravo_locked = True
            return

        player = next((s for s in self.skipped_singles if s['id'] == player_id), None)
        if player:
            self.skipped_singles.remove(player)
            self.queue_singles.insert(0, player)
            self.next_player_alfa_bravo_id = player_id
            self.next_player_alfa_bravo_locked = True
            return
        
        player = next((p for p in self.skipped_couples2 if p['id'] == player_id), None)
        if player:
            self.skipped_couples2.remove(player)
            self.queue_couples2.insert(0, player)
            self.next_player_alfa_bravo_id2 = player_id
            self.next_player_alfa_bravo_locked2 = True
            return  
        
        player = next((s for s in self.skipped_singles2 if s['id'] == player_id), None) 
        if player:
            self.skipped_singles2.remove(player)
            self.queue_singles2.insert(0, player)
            self.next_player_alfa_bravo_id2 = player_id
            self.next_player_alfa_bravo_locked2 = True
            return  
        
        player = next((p for p in self.skipped_charlie if p['id'] == player_id), None)
        if player:
            self.skipped_charlie.remove(player)
            self.queue_charlie.insert(0, player)
            self.next_player_charlie_id = player_id
            self.next_player_charlie_name = self.get_player_name(player_id)
            self.next_player_charlie_locked = True
            return
        
        # Aggiungi questo blocco per gestire gli skippati statico
        player = next((p for p in self.skipped_statico if p['id'] == player_id), None)
        if player:
            self.skipped_statico.remove(player)
            self.queue_statico.insert(0, player)
            self.next_player_statico_id = player_id
            self.next_player_statico_name = self.get_player_name(player_id)
            self.next_player_statico_locked = True
            return
        
        raise ValueError(f"Player {player_id} not found in any skipped list")

    def start_charlie_game(self) -> None:
        """Avvia un gioco sulla pista Charlie"""
        if self.next_player_charlie_id:
            self.current_player_charlie = {'id': self.next_player_charlie_id, 'arrival': self.get_current_time()}
            self.CHARLIE_next_available = self.get_current_time() + datetime.timedelta(minutes=self.T_charlie)
            self.player_start_times[self.current_player_charlie['id']] = self.get_current_time()
            self.player_in_charlie = True
            # Rimuovi il giocatore dalla coda
            self.queue_charlie = [p for p in self.queue_charlie if p['id'] != self.next_player_charlie_id]
            # Imposta il prossimo giocatore
            if self.queue_charlie:
                self.next_player_charlie_id = self.queue_charlie[0]['id']
                self.next_player_charlie_name = self.get_player_name(self.next_player_charlie_id)
                self.next_player_charlie_locked = True
            else:
                self.next_player_charlie_id = None
                self.next_player_charlie_name = None
                self.next_player_charlie_locked = False

    def get_durations(self) -> Dict[str, str]:
        """Restituisce le durate dei giocatori attuali in pista formattate in minuti:secondi"""
        durations = {}
        now = self.get_current_time()
        if self.current_player_alfa:
            player_id = self.current_player_alfa['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['alfa'] = f"{minutes:02}:{seconds:02}"
        if self.current_player_bravo:
            player_id = self.current_player_bravo['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['bravo'] = f"{minutes:02}:{seconds:02}"

        if self.current_player_alfa2:
            player_id = self.current_player_alfa2['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['alfa2'] = f"{minutes:02}:{seconds:02}"   

        if self.current_player_bravo2:
            player_id = self.current_player_bravo2['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['bravo2'] = f"{minutes:02}:{seconds:02}"  

        if self.current_player_charlie:
            player_id = self.current_player_charlie['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['charlie'] = f"{minutes:02}:{seconds:02}"
        if self.current_player_delta:
            player_id = self.current_player_delta['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['delta'] = f"{minutes:02}:{seconds:02}"
        if self.current_player_echo:
            player_id = self.current_player_echo['id']
            start_time = self.player_start_times.get(player_id)
            if start_time:
                duration_seconds = (now - start_time).total_seconds()
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                durations['echo'] = f"{minutes:02}:{seconds:02}"        
        return durations

    def delete_player(self, player_id: str) -> None:
        """Elimina un giocatore dalla coda"""
        self.queue_couples = [p for p in self.queue_couples if p['id'] != player_id]
        self.queue_singles = [p for p in self.queue_singles if p['id'] != player_id]
        self.queue_couples2 = [p for p in self.queue_couples2 if p['id'] != player_id]
        self.queue_singles2 = [p for p in self.queue_singles2 if p['id'] != player_id]
        self.queue_charlie = [p for p in self.queue_charlie if p['id'] != player_id]
        self.queue_statico = [p for p in self.queue_statico if p['id'] != player_id]
        self.skipped_couples = [p for p in self.skipped_couples if p['id'] != player_id]
        self.skipped_singles = [p for p in self.skipped_singles if p['id'] != player_id]
        self.skipped_couples2 = [p for p in self.skipped_couples2 if p['id'] != player_id]
        self.skipped_singles2 = [p for p in self.skipped_singles2 if p['id'] != player_id]
        self.skipped_charlie = [p for p in self.skipped_charlie if p['id'] != player_id]
        self.skipped_statico = [p for p in self.skipped_statico if p['id'] != player_id]

        # Check if the deleted player was the next player in the queue
        if self.next_player_alfa_bravo_id == player_id:
            self.next_player_alfa_bravo_id = None
            self.next_player_alfa_bravo_name = None
            self.next_player_alfa_bravo_locked = False
            self.update_next_player()

        if self.next_player_alfa_bravo_id2 == player_id:
            self.next_player_alfa_bravo_id2 = None
            self.next_player_alfa_bravo_name2 = None
            self.next_player_alfa_bravo_locked2 = False
            self.update_next_player2()

        if self.next_player_charlie_id == player_id:
            self.next_player_charlie_id = None
            self.next_player_charlie_name = None
            self.next_player_charlie_locked = False
            self.update_next_player()

         # Check if the deleted player was the next player in the queue
        if self.next_player_statico_id == player_id:
            self.next_player_statico_id = None
            self.next_player_statico_name = None
            self.next_player_statico_locked = False
            self.update_next_player()
        
        

    def calculate_blue_waiting_time(self, current_blu: int, len_giallo: int) -> float:
        """
        Calcola il tempo di attesa per un giocatore blu.
        
        Args:
            current_blu: posizione del giocatore blu analizzato
            len_giallo: numero totale di giocatori gialli
            
        Returns:
            float: tempo di attesa in minuti
        """
        # CALCOLO DI N_GIALLO RELATIVAMENTE AL BLU analizzato
        if current_blu <= len_giallo:
            N_giallo = current_blu
        else:
            N_giallo = len_giallo
            
        # TEMPO DI ATTESA DEL BLU analizzato
        min_att = self.T_mid * N_giallo + self.T_single * (current_blu - 1)
        return min_att

    def calculate_yellow_waiting_time(self, current_giallo: int, len_blu: int, dt_total: float, dt_mid: float, dt_single: float) -> float:
        """
        Calcola il tempo di attesa per un giocatore giallo.
        
        Args:
            current_giallo: posizione del giocatore giallo analizzato
            len_blu: numero totale di giocatori blu
            dt_total: tempo medio totale esecuzione giallo
            dt_mid: mezzo tempo giallo, tempo di sblocco del tasterino
            dt_single: tempo medio totale esecuzione blu
            
        Returns:
            float: tempo di attesa in minuti
        """
        
        if dt_total <= (dt_single + dt_mid) and (current_giallo <= len_blu):
            min_att = dt_single * (current_giallo - 1) + dt_mid * (current_giallo - 1)
        elif dt_total <= (dt_single + dt_mid):
            min_att = dt_single * len_blu + dt_mid * len_blu + dt_total * (current_giallo - len_blu)
        else:
            min_att = dt_total * (current_giallo - 1)
        
        return min_att

    def simulate_schedule(self) -> Dict[str, datetime.datetime]:
        now = self.get_current_time()
        estimated_times = {}
        
        # Calcolo lunghezze code
        len_giallo = len(self.queue_couples)
        len_blu = len(self.queue_singles)
        
        # Per ogni giocatore blu (singles)
        for current_blu, player in enumerate(self.queue_singles, 1):
            # Calcola il tempo di attesa
            min_att = self.calculate_blue_waiting_time(
                current_blu=current_blu,
                len_giallo=len_giallo
            )
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        # Per ogni giocatore giallo (couples)
        for current_giallo, player in enumerate(self.queue_couples, 1):
            min_att = self.calculate_yellow_waiting_time(
                current_giallo=current_giallo,
                len_blu=len_blu,
                dt_total=self.T_total,
                dt_mid=self.T_mid,
                dt_single=self.T_single
            )
            estimated_times[player['id']] = now + datetime.timedelta(minutes=min_att)
        
        return estimated_times

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

