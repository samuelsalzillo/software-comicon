# --- NUOVA Funzione Load History Timer Charlie ---
import logging
import os
import sqlite3


def load_charlie_timer_history_from_db(sqlite_lock,backend):
    logging.debug("[LOAD CHARLIE TIMERS] Tentativo caricamento storico timer Charlie da DB.")
    try:
        with sqlite_lock:
            logging.debug("[LOAD CHARLIE TIMERS] Lock DB acquisito.")
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            # Seleziona solo le durate, ordinate per data (opzionale ma buono)
            cursor.execute("""
                SELECT timer_duration_minutes
                FROM charlie_timer_scores
                ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            conn.close()
        logging.debug(f"[LOAD CHARLIE TIMERS] Lock DB rilasciato. Trovati {len(rows)} record timer.")

        # Pulisci la lista esistente PRIMA di caricare
        backend.charlie_timer_history.clear()
        logging.debug("[LOAD CHARLIE TIMERS] Lista backend.charlie_timer_history resettata.")

        loaded_count = 0
        for row in rows:
            try:
                duration_minutes = float(row[0])
                backend.charlie_timer_history.append(duration_minutes)
                loaded_count += 1
            except (ValueError, TypeError, IndexError) as e:
                logging.warning(f"[LOAD CHARLIE TIMERS] Errore conversione/lettura durata timer: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD CHARLIE TIMERS] Caricamento completato. Caricati {loaded_count} record timer.")

        # Ricalcola subito la media T_charlie dopo il caricamento
        backend.update_averages()
        logging.info("[LOAD CHARLIE TIMERS] Media T_charlie ricalcolata post-caricamento.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD CHARLIE TIMERS] Errore Database durante caricamento storico timer: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD CHARLIE TIMERS] Errore generico durante caricamento storico timer: {e}", exc_info=True)