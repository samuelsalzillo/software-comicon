import logging
import os
import sqlite3


def load_mid_times_from_db(sqlite_lock,backend):
    logging.debug("[LOAD MID TIMES] Tentativo caricamento storico mid times da DB.")
    loaded_rows = 0
    appended_mid1 = 0
    appended_mid2 = 0
    try:
        with sqlite_lock:
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT couple_type, mid_duration_minutes
                FROM mid_times ORDER BY recorded_at ASC
            """)
            rows = cursor.fetchall()
            loaded_rows = len(rows)
            conn.close()
        logging.debug(f"[LOAD MID TIMES] Lock DB rilasciato. Trovati {loaded_rows} record mid time nel DB.")

        # Pulisci liste
        backend.couple_history_mid.clear()
        backend.couple_history_mid2.clear()
        logging.debug("[LOAD MID TIMES] Liste backend couple_history_mid e mid2 resettate.")

        for i, row in enumerate(rows):
            try:
                couple_type, mid_duration = row
                duration_minutes = float(mid_duration)
                logging.debug(f"[LOAD MID TIMES] Processing row {i+1}/{loaded_rows}: type={couple_type}, duration={duration_minutes:.4f}")

                if couple_type == 'couple1':
                    backend.couple_history_mid.append(duration_minutes)
                    appended_mid1 += 1
                    logging.debug(f"  -> Appended to couple_history_mid (new size: {len(backend.couple_history_mid)})")
                elif couple_type == 'couple2':
                    backend.couple_history_mid2.append(duration_minutes)
                    appended_mid2 += 1
                    logging.debug(f"  -> Appended to couple_history_mid2 (new size: {len(backend.couple_history_mid2)})")
                else:
                     logging.warning(f"  -> Unknown couple_type '{couple_type}' in mid_times table, row ignored.")

            except Exception as e:
                logging.warning(f"[LOAD MID TIMES] Errore processando riga {i+1}: {row}. Errore: {e}. Riga ignorata.")

        logging.info(f"[LOAD MID TIMES] Caricamento completato. Righe DB: {loaded_rows}. Appended Mid1: {appended_mid1}. Appended Mid2: {appended_mid2}.")
        logging.info(f"  -> Final backend list sizes: mid1={len(backend.couple_history_mid)}, mid2={len(backend.couple_history_mid2)}")

        # Ricalcola medie (DOPO aver caricato TUTTI i dati necessari, quindi magari chiamalo una sola volta alla fine di tutti i load_)
        # backend.update_averages() # Sposta questa chiamata alla fine di tutte le funzioni load_

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD MID TIMES] Errore Database: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD MID TIMES] Errore generico: {e}", exc_info=True)