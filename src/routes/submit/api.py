import logging
import os
import sqlite3

from flask import Blueprint, jsonify, request
from ...utils.database import get_lock,execute_with_retry
from ...utils.model import get_game_backend, set_game_backend
from ...utils import date

submit = Blueprint('submit',__name__,url_prefix='')

@submit.route('/submit_combined_score', methods=['POST'])
def submit_combined_score():
    backend = get_game_backend()
    sqlite_lock = get_lock()
    data = request.json
    logging.debug(f"Received /submit_combined_score data: {data}")
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    player_type = data.get('player_type') # 'couple', 'single', 'couple2', 'single2'
    timer_duration_str = data.get('timer_duration_minutes')
    official_score_str = data.get('official_score_minutes')

    # Validazione input base
    if not all([player_id, player_name, player_type,
                timer_duration_str is not None, official_score_str is not None]):
        logging.warning("Submit combined score failed: Missing data.")
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio finale mancanti."), 400

    try:
        timer_duration = float(timer_duration_str)
        official_score = float(official_score_str)
        now = date.get_current_time()
        score_formatted = date.format_time(official_score)

        logging.info(f"[COMBINED SCORE SUBMIT] Player: {player_id} ({player_name}), Type: {player_type}, Timer: {timer_duration:.4f}, Score: {official_score:.4f} ({score_formatted})")

        # 1. Salva Timer Duration nel DB per le medie
        try:
            with sqlite_lock:
                conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                cursor = conn.cursor()
                # Inserisci il record specifico del timer
                execute_with_retry(
                    cursor,
                    "INSERT INTO average_times (player_type, timer_duration_minutes, recorded_at) VALUES (?, ?, ?)",
                    (player_type, timer_duration, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[AVG TIME DB SAVE] Success for {player_id} ({player_type}).")
        except sqlite3.Error as db_err:
            logging.error(f"[AVG TIME DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            # Potremmo decidere di continuare comunque o ritornare errore? Per ora continuiamo.
        except Exception as e:
            logging.error(f"[AVG TIME DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            # Continuiamo

        # 2. Salva Official Score nel DB per la classifica
        try:
            with sqlite_lock:
                conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                cursor = conn.cursor()
                # Determina il player_type corretto per la tabella scoring ('couple' o 'single')
                scoring_player_type = 'couple' if player_type in ('couple', 'couple2') else 'single'
                execute_with_retry(
                    cursor,
                    "INSERT INTO scoring (player_type, player_id, player_name, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    (scoring_player_type, player_id, player_name, official_score, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[SCORING DB SAVE] Success for {player_id} ({scoring_player_type}).")
        except sqlite3.Error as db_err:
            logging.error(f"[SCORING DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore DB salvataggio score: {db_err}"), 500
        except Exception as e:
            logging.error(f"[SCORING DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore generico salvataggio score: {e}"), 500


        # 3. Chiama il metodo backend per aggiornare medie e stato interno
        #    Passa SIA timer_duration SIA official_score
        try:
            if player_type == 'couple':
                # Calcola mid_time_approx se necessario per T_mid (come faceva prima button_press)
                # start_time = backend.player_start_times.get(player_id) # Start time dovrebbe essere già stato rimosso da record_...
                # alfa_avail = backend.localize_time(backend.ALFA_next_available)
                # mid_time_approx = (alfa_avail - start_time).total_seconds() / 60 if start_time and alfa_avail > start_time else backend.T_mid
                backend.record_couple_game(timer_duration, official_score)
            elif player_type == 'single':
                backend.record_single_game(timer_duration, official_score)
            elif player_type == 'couple2':
                backend.record_couple2_game(timer_duration, official_score)
            elif player_type == 'single2':
                backend.record_single2_game(timer_duration, official_score)
            logging.debug(f"Backend record method called successfully for {player_id}")
        except Exception as e:
             logging.error(f"Error calling backend record method for {player_id} ({player_type}): {e}", exc_info=True)
             # Anche se c'è errore qui, i dati sono salvati, quindi procedi col check qualifica


        # 4. Controlla la qualifica usando l'OFFICIAL SCORE
        scoring_player_type = 'couple' if player_type in ('couple', 'couple2') else 'single'
        logging.debug(f"Checking qualification for {player_id} with score={official_score}, type={scoring_player_type}") # Log prima del check
        is_qualified, reason = backend.check_qualification(official_score, scoring_player_type)
        logging.info(f"[COMBINED QUAL CHECK] Player: {player_id}, Score: {official_score:.4f}, Qualified: {is_qualified}, Reason: {reason}")


        # 5. Ritorna il risultato al frontend
        set_game_backend(backend)
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            # Passa indietro i dati necessari per il modal contatti
            player_id=player_id,
            player_name=player_name,
            recorded_score=official_score, # Punteggio ufficiale che ha qualificato
            player_type=scoring_player_type # Tipo per il modal contatti ('couple' o 'single')
        )

    except ValueError as ve:
        logging.error(f"Invalid numeric format in submit_combined_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato numerico non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[COMBINED SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio finale: {e}"), 500

@submit.route('/submit_charlie_score', methods=['POST'])
def submit_charlie_score():
    backend = get_game_backend()
    sqlite_lock = get_lock()
    data = request.json
    logging.debug(f"Received /submit_charlie_score data: {data}")
    player_id = data.get('player_id')
    player_name = data.get('player_name') # Ricevi anche il nome
    minutes_str = data.get('minutes')
    seconds_str = data.get('seconds')
    milliseconds_str = data.get('milliseconds')

    if not all([player_id, player_name is not None, minutes_str is not None, seconds_str is not None, milliseconds_str is not None]):
        logging.warning("Submit charlie score failed: Missing data.")
        return jsonify(success=False, qualified=False, reason=None, error="Dati punteggio mancanti."), 400

    try:
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        milliseconds = int(milliseconds_str)

        if not (0 <= minutes < 60 and 0 <= seconds < 60 and 0 <= milliseconds < 1000):
             raise ValueError("Valori tempo fuori range.")

        # Calcola il punteggio ufficiale in minuti (float)
        manual_score_minutes = minutes + (seconds / 60.0) + (milliseconds / 60000.0)
        score_formatted = date.format_time(manual_score_minutes)
        now = date.get_current_time()

        logging.info(f"[CHARLIE SCORE SUBMIT] Player: {player_id} ({player_name}), Manual Score: {manual_score_minutes:.4f} min ({score_formatted})")

        # 1. Salva nella tabella scoring
        try:
            with sqlite_lock:
                conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    ('charlie', player_id, player_name, manual_score_minutes, now)
                )
                conn.commit()
                conn.close()
            logging.info(f"[CHARLIE SCORE DB SAVE] Success for {player_id}.")
        except sqlite3.Error as db_err:
            logging.error(f"[CHARLIE SCORE DB SAVE] Failed for {player_id}: {db_err}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore DB salvataggio punteggio: {db_err}"), 500
        except Exception as e:
            logging.error(f"[CHARLIE SCORE DB SAVE] Failed (General Error) for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore generico salvataggio punteggio: {e}"), 500

        # 2. Aggiungi alla history ufficiale per leaderboard in-memory (se get_leaderboard la usa)
        backend.charlie_history.append((player_id, manual_score_minutes))
        logging.debug(f"Added manual score to backend.charlie_history (new size: {len(backend.charlie_timer_history)})")

        # 3. Controlla la qualifica
        is_qualified, reason = backend.check_qualification(manual_score_minutes, 'charlie')
        logging.info(f"[CHARLIE QUAL CHECK] Player: {player_id}, Score: {manual_score_minutes:.4f}, Qualified: {is_qualified}, Reason: {reason}")

        # 4. Ritorna il risultato al frontend
        set_game_backend(backend)
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            # Passa indietro i dati necessari per il modal contatti
            player_id=player_id,
            player_name=player_name,
            recorded_score=manual_score_minutes, # Il punteggio manuale
            player_type='charlie'
        )

    except ValueError as ve:
        logging.error(f"Invalid time format in submit_charlie_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato tempo non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[CHARLIE SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio: {e}"), 500
