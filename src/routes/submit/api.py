import logging

from flask import Blueprint, jsonify, request
from ...repository import get_scoring_repository, get_average_times_repository
from ...utils.model import get_game_backend, set_game_backend
from ...utils import date

submit = Blueprint('submit',__name__,url_prefix='')

@submit.route('/submit_combined_score', methods=['POST'])
def submit_combined_score():
    """
    Submit combined score using repository pattern.
    """
    backend = get_game_backend()
    scoring_repo = get_scoring_repository()
    avg_times_repo = get_average_times_repository()

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
        score_formatted = date.format_time_into_mmss(official_score)

        logging.info(f"[COMBINED SCORE SUBMIT] Player: {player_id} ({player_name}), Type: {player_type}, Timer: {timer_duration:.4f}, Score: {official_score:.4f} ({score_formatted})")

        # 1. Salva Timer Duration usando repository
        try:
            avg_times_repo.save_average(
                player_type=player_type,
                timer_duration_minutes=timer_duration,
                official_score_minutes=official_score
            )
            logging.info(f"[AVG TIME REPO SAVE] Success for {player_id} ({player_type}).")
        except Exception as e:
            logging.error(f"[AVG TIME REPO SAVE] Failed for {player_id}: {e}", exc_info=True)
            # Continuiamo comunque

        # 2. Salva Official Score usando repository
        try:
            # Determina il player_type corretto per la tabella scoring
            scoring_player_type = 'couple' if player_type in ('couple', 'couple2') else 'single'

            scoring_repo.save_score(
                player_id=player_id,
                player_name=player_name,
                player_type=scoring_player_type,
                score=official_score
            )
            logging.info(f"[SCORING REPO SAVE] Success for {player_id} ({scoring_player_type}).")
        except Exception as e:
            logging.error(f"[SCORING REPO SAVE] Failed for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore salvataggio score: {e}"), 500

        # 3. Chiama il metodo backend per aggiornare medie e stato interno
        try:
            if player_type == 'couple':
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
        logging.debug(f"Checking qualification for {player_id} with score={official_score}, type={scoring_player_type}")
        is_qualified, reason = backend.check_qualification(official_score, scoring_player_type)
        logging.info(f"[COMBINED QUAL CHECK] Player: {player_id}, Score: {official_score:.4f}, Qualified: {is_qualified}, Reason: {reason}")

        # 5. Ritorna il risultato al frontend
        set_game_backend(backend)
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            player_id=player_id,
            player_name=player_name,
            recorded_score=official_score,
            player_type=scoring_player_type
        )

    except ValueError as ve:
        logging.error(f"Invalid numeric format in submit_combined_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato numerico non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[COMBINED SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio finale: {e}"), 500

@submit.route('/submit_charlie_score', methods=['POST'])
def submit_charlie_score():
    """
    Submit Charlie score using repository pattern.
    """
    backend = get_game_backend()
    scoring_repo = get_scoring_repository()

    data = request.json
    logging.debug(f"Received /submit_charlie_score data: {data}")

    player_id = data.get('player_id')
    player_name = data.get('player_name')
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
        score_formatted = date.format_time_into_mmss(manual_score_minutes)

        logging.info(f"[CHARLIE SCORE SUBMIT] Player: {player_id} ({player_name}), Manual Score: {manual_score_minutes:.4f} min ({score_formatted})")

        # 1. Salva nella tabella scoring usando repository
        try:
            scoring_repo.save_score(
                player_id=player_id,
                player_name=player_name,
                player_type='charlie',
                score=manual_score_minutes
            )
            logging.info(f"[CHARLIE SCORE REPO SAVE] Success for {player_id}.")
        except Exception as e:
            logging.error(f"[CHARLIE SCORE REPO SAVE] Failed for {player_id}: {e}", exc_info=True)
            return jsonify(success=False, qualified=False, reason=None, error=f"Errore salvataggio punteggio: {e}"), 500

        # 2. Aggiungi alla history in-memory
        backend.charlie_history.append((player_id, manual_score_minutes))
        logging.debug(f"Added manual score to backend.charlie_history")

        # 3. Controlla la qualifica
        is_qualified, reason = backend.check_qualification(manual_score_minutes, 'charlie')
        logging.info(f"[CHARLIE QUAL CHECK] Player: {player_id}, Score: {manual_score_minutes:.4f}, Qualified: {is_qualified}, Reason: {reason}")

        # 4. Ritorna il risultato al frontend
        set_game_backend(backend)
        return jsonify(
            success=True,
            qualified=is_qualified,
            reason=reason,
            player_id=player_id,
            player_name=player_name,
            recorded_score=manual_score_minutes,
            player_type='charlie'
        )

    except ValueError as ve:
        logging.error(f"Invalid time format in submit_charlie_score: {ve}. Data: {data}")
        return jsonify(success=False, qualified=False, reason=None, error=f"Formato tempo non valido: {ve}"), 400
    except Exception as e:
        logging.error(f"[CHARLIE SCORE SUBMIT] Failed processing score for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, qualified=False, reason=None, error=f"Errore elaborazione punteggio: {e}"), 500
