import logging
import os
import sqlite3


def load_scores_from_db(sqlite_lock,backend):
    """
    Carica i punteggi NUMERICI dalla tabella 'scoring' nelle liste
    di storico del backend all'avvio dell'applicazione.
    Queste liste sono usate per calcolare le medie T_mid, T_total, etc.
    """
    logging.debug("[LOAD SCORES] Tentativo caricamento punteggi da DB.")
    try:
        # >>> ACQUISISCI IL LOCK <<<
        with sqlite_lock:
            logging.debug("[LOAD SCORES] Lock DB acquisito.")
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()

            # Seleziona il tipo di giocatore e il punteggio numerico
            # Ordina per data creazione se vuoi processarli in ordine cronologico
            cursor.execute("""
                SELECT player_type, player_id, score
                FROM scoring
                WHERE score IS NOT NULL
                ORDER BY created_at ASC
            """)
            rows = cursor.fetchall()
            conn.close()
        # >>> RILASCIA IL LOCK <<<
        logging.debug(f"[LOAD SCORES] Lock DB rilasciato. Trovati {len(rows)} punteggi.")

        # Pulisci le liste esistenti nel backend PRIMA di caricarle
        backend.couple_history_total.clear()
        backend.single_history.clear()
        backend.couple_history_total2.clear()
        backend.single_history2.clear()
        backend.charlie_history.clear()
        backend.statico_history.clear()
        logging.debug("[LOAD SCORES] Liste storico backend resettate.")

        loaded_counts = {'couple': 0, 'single': 0, 'charlie': 0, 'statico': 0}

        for row in rows:
            player_type, player_id, score_value = row
            try:
                score_minutes = float(score_value)
                if player_type == 'couple':
                    backend.couple_history_total.append((player_id, score_minutes))
                elif player_type == 'single':
                    backend.single_history.append((player_id, score_minutes))
                elif player_type == 'couple2':
                    backend.couple_history_total2.append((player_id, score_minutes))
                elif player_type == 'single2':
                    backend.single_history2.append((player_id, score_minutes))
                elif player_type == 'charlie':
                    backend.charlie_history.append((player_id, score_minutes))
                elif player_type == 'statico':
                    backend.statico_history.append((player_id, score_minutes))
            except Exception as e:
                logging.error(f"Error processing score row {row}: {e}")

        logging.info(f"[LOAD SCORES] Caricamento completato. Conteggi: Coppie={loaded_counts['couple']}, Singoli={loaded_counts['single']}, Charlie={loaded_counts['charlie']}, Statico={loaded_counts['statico']}")

        # Dopo aver caricato le storie, ricalcola subito le medie iniziali
        backend.update_averages()
        logging.info("[LOAD SCORES] Medie iniziali ricalcolate.")

    except sqlite3.Error as db_err:
         logging.error(f"[LOAD SCORES] Errore Database durante caricamento punteggi: {db_err}", exc_info=True)
    except Exception as e:
        logging.error(f"[LOAD SCORES] Errore generico durante caricamento punteggi: {e}", exc_info=True)



