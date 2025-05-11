import logging
import os
import sqlite3


def load_average_times_from_db(sqlite_lock,backend):
    logging.debug("[LOAD AVG TIMES] Tentativo caricamento storico timer per medie da DB.")
    loaded_rows = 0 # Contatore righe DB
    appended_couple = 0 # Contatore append coppie
    appended_single = 0 # Contatore append singoli
    try:
        with sqlite_lock:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            # ... (connessione e cursor) ...
            cursor.execute("""
                SELECT player_type, timer_duration_minutes
                FROM average_times ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            loaded_rows = len(rows) # Quante righe dal DB?
            conn.close()
        logging.debug(f"[LOAD AVG TIMES] Lock DB rilasciato. Trovati {loaded_rows} record timer nel DB.")

        # Pulisci liste
        backend.couple_timer_history.clear()
        backend.single_timer_history.clear()
        backend.single_timer_history2.clear()
        logging.debug("[LOAD AVG TIMES] Liste backend *timer* resettate.")

        for i, row in enumerate(rows): # Aggiunto indice per logging
            try:
                player_type, timer_duration = row
                duration_minutes = float(timer_duration)
                logging.debug(f"[LOAD AVG TIMES] Processing row {i+1}/{loaded_rows}: type={player_type}, duration={duration_minutes:.4f}") # LOG RIGA

                if player_type in ('couple', 'couple2'):
                    backend.couple_timer_history.append(duration_minutes)
                    appended_couple += 1
                    logging.debug(f"  -> Appended to couple_timer_history (new size: {len(backend.couple_timer_history)})") # LOG APPEND
                elif player_type in ('single'):
                    backend.single_timer_history.append(duration_minutes)
                    appended_single += 1
                    logging.debug(f"  -> Appended to single_timer_history (new size: {len(backend.single_timer_history)})") # LOG APPEND
                elif player_type in ('single2'):
                    backend.single_timer_history2.append(duration_minutes)
                    appended_single += 1
                    logging.debug(f"  -> Appended to single_timer_history (new size: {len(backend.single_timer_history)})") # LOG APPEND
                else:
                     logging.warning(f"  -> Unknown player_type '{player_type}' in average_times table, row ignored.")

            except Exception as e:
                logging.warning(f"[LOAD AVG TIMES] Errore processando riga {i+1}: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD AVG TIMES] Caricamento completato. Righe DB: {loaded_rows}. Appended Couple Timers: {appended_couple}. Appended Single Timers: {appended_single}.")
        logging.info(f"  -> Final backend list sizes: couple_timer={len(backend.couple_timer_history)}, single_timer={len(backend.single_timer_history)}")

        # Ricalcola medie
        backend.update_averages() # Chiamato DOPO il caricamento
        logging.info("[LOAD AVG TIMES] Medie ricalcolate post-caricamento timers.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD AVG TIMES] Errore Database: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD AVG TIMES] Errore generico: {e}", exc_info=True)
