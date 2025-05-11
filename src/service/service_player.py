import logging
import os
import sqlite3

from flask import request, jsonify, url_for

from ..utils.database import get_lock, execute_with_retry
from ..utils import date
from ..utils.model import get_game_backend, set_game_backend
from . import service_game_backend

def service_save_contact():
    sqlite_lock = get_lock()
    data = request.json
    logging.debug(f"Received data for /save_contact_info: {data}")
    player_id = data.get('player_id')           # Es. GIALLO 01
    player_name = data.get('player_name')       # Es. Nome Squadra (se esiste) o ID
    first_name = data.get('first_name')       # Nome contatto
    last_name = data.get('last_name')         # Cognome contatto
    phone_number = data.get('phone_number')   # Telefono contatto
    score_minutes_str = data.get('score_minutes') # Punteggio che ha qualificato
    player_type = data.get('player_type')       # couple / single / couple2 / single2
    qualification_reason = data.get('qualification_reason') # best_today / top_3_overall

    if not all([player_id, player_name, first_name, last_name, phone_number,
                score_minutes_str is not None, player_type, qualification_reason]):
        logging.warning("Save contact info failed: Missing data.")
        return jsonify(success=False, message="Dati di contatto mancanti o incompleti."), 400

    try:
        score_float = float(score_minutes_str)
        score_formatted = date.format_time(score_float)
        qualification_date = date.get_current_time().strftime('%Y-%m-%d')
        timestamp = date.get_current_time()

        # Normalize player_type to match the allowed values in the database
        normalized_player_type = player_type.lower()
        if normalized_player_type in ('couple2', 'single2'):
            normalized_player_type = normalized_player_type[:-1]  # Rimuove il "2"

        if normalized_player_type not in ('couple', 'single',        'charlie'):
            logging.error(f"Invalid player_type: {normalized_player_type}")
            return jsonify(success=False, message="Tipo giocatore non valido."), 400

        with sqlite_lock:  # Ensure the lock is used to serialize database access
            conn = sqlite3.connect(os.environ.get('SQLITE_DB_PATH'))
            cursor = conn.cursor()
            logging.info(f"[CONTACT SAVE] ID={player_id}, Contact={first_name} {last_name}, Phone={phone_number}, Score={score_formatted}, Reason={qualification_reason}")
            execute_with_retry(
                cursor,
                """
                INSERT INTO qualified_players
                (player_id, player_name, first_name, last_name, phone_number, score_minutes, score_formatted, player_type, qualification_reason, qualification_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player_id, player_name, first_name, last_name, phone_number,
                    score_float, score_formatted, normalized_player_type, qualification_reason,
                    qualification_date, timestamp
                )
            )
            conn.commit()
            conn.close()
        logging.info("[CONTACT SAVE] Success.")
        return jsonify(success=True, message="Dati di contatto salvati con successo!")

    except ValueError:
         logging.error(f"Invalid score format in save_contact_info: {score_minutes_str}")
         return jsonify(success=False, message="Punteggio non valido nel salvataggio contatti."), 400
    except Exception as e:
        logging.error(f"[CONTACT SAVE] Failed for {player_id}: {e}", exc_info=True)
        return jsonify(success=False, message=f"Errore DB durante salvataggio dati: {e}"), 500

def simulate_player():
    backend = get_game_backend()
    couples_board, singles_board, couples2_board, singles2_board, charlie_board, statico_board = backend.get_waiting_board()
    next_player_alfa_bravo_id = backend.next_player_alfa_bravo_id
    next_player_alfa_bravo_id2 = backend.next_player_alfa_bravo_id2
    next_player_charlie_id = backend.next_player_charlie_id
    next_player_charlie_name = backend.next_player_charlie_name

    # now = date.get_current_time()
    # alfa_remaining = max(0, (backend.localize_time(backend.ALFA_next_available) - now).total_seconds() / 60)
    # bravo_remaining = max(0, (backend.localize_time(backend.BRAVO_next_available) - now).total_seconds() / 60)
    # alfa2_remaining = max(0, (backend.localize_time(backend.ALFA_next_available2) - now).total_seconds() / 60)
    # bravo2_remaining = max(0, (backend.localize_time(backend.BRAVO_next_available2) - now).total_seconds() / 60) fixme non è utilizzato cancelliamo?

    durations = backend.get_durations()
    formatted_charlie_board = service_game_backend.format_list(charlie_board, backend.player_names)

    formatted_couples_board = service_game_backend.format_list(couples_board, backend.player_names)

    formatted_singles_board = service_game_backend.format_list(singles_board, backend.player_names)

    formatted_couples2_board = service_game_backend.format_list(couples2_board, backend.player_names)

    formatted_singles2_board = service_game_backend.format_list(singles2_board, backend.player_names)

    # Aggiungo la board per statico
    formatted_statico_board = service_game_backend.format_list(statico_board, backend.player_names)

    next_player_alfa_bravo_name = backend.get_player_name(
        next_player_alfa_bravo_id) if next_player_alfa_bravo_id else None
    next_player_alfa_bravo_name2 = backend.get_player_name(
        next_player_alfa_bravo_id2) if next_player_alfa_bravo_id2 else None
    current_player_alfa = backend.current_player_alfa
    current_player_bravo = backend.current_player_bravo
    current_player_alfa2 = backend.current_player_alfa2
    current_player_bravo2 = backend.current_player_bravo2
    current_player_charlie = backend.current_player_charlie

    # single_in_alfa = (
    #         isinstance(backend.current_player_alfa, dict) and
    #         'name' in backend.current_player_alfa and
    #         backend.current_player_alfa['name'] == "BLU"
    # )
    # couple_in_alfa = (
    #         isinstance(backend.current_player_alfa, dict) and
    #         'name' in backend.current_player_alfa and
    #         backend.current_player_alfa['name'] == "GIALLO"
    # )
    # couple_in_bravo = (
    #         isinstance(backend.current_player_bravo, dict) and
    #         'name' in backend.current_player_bravo and1            fixme non utilizzato cosa facciamo?
    #         backend.current_player_bravo['name'] == "GIALLO"
    # )
    # single_in_alfa2 = (
    #         isinstance(backend.current_player_alfa2, dict) and
    #         'name' in backend.current_player_alfa2 and
    #         backend.current_player_alfa2['name'] == "BLU"
    # )
    # couple_in_alfa2 = (
    #         isinstance(backend.current_player_alfa2, dict) and
    #         'name' in backend.current_player_alfa2 and
    #         backend.current_player_alfa2['name'] == "GIALLO"
    # )
    # couple_in_bravo2 = (
    #         isinstance(backend.current_player_bravo2, dict) and
    #         'name' in backend.current_player_bravo2 and
    #         backend.current_player_bravo2['name'] == "GIALLO"
    # )

    now = date.get_current_time()
    backend.ALFA_next_available = backend.localize_time(backend.ALFA_next_available)
    backend.BRAVO_next_available = backend.localize_time(backend.BRAVO_next_available)
    backend.ALFA_next_available2 = backend.localize_time(backend.ALFA_next_available2)
    backend.BRAVO_next_available2 = backend.localize_time(backend.BRAVO_next_available2)
    backend.CHARLIE_next_available = backend.localize_time(backend.CHARLIE_next_available)
    backend.DELTA_next_available = backend.localize_time(backend.DELTA_next_available)
    backend.ECHO_next_available = backend.localize_time(backend.ECHO_next_available)

    alfa_remaining = max(0, (backend.ALFA_next_available - now).total_seconds() / 60)
    bravo_remaining = max(0, (backend.BRAVO_next_available - now).total_seconds() / 60)
    alfa2_remaining = max(0, (backend.ALFA_next_available2 - now).total_seconds() / 60)
    bravo2_remaining = max(0, (backend.BRAVO_next_available2 - now).total_seconds() / 60)
    charlie_remaining = max(0, (backend.CHARLIE_next_available - now).total_seconds() / 60)
    delta_remaining = max(0, (backend.DELTA_next_available - now).total_seconds() / 60)
    echo_remaining = max(0, (backend.ECHO_next_available - now).total_seconds() / 60)

    can_stop_couple1 = backend.can_stop_couple()
    can_stop_couple2 = backend.can_stop_couple2()
    # Nota: Per i singoli, lo stop è sempre possibile se il gioco è attivo
    can_stop_single1 = backend.current_player_alfa is not None and backend.current_player_alfa.get('id', '').startswith(
        "BLU")
    can_stop_single2 = backend.current_player_alfa2 is not None and backend.current_player_alfa2.get('id',
                                                                                                     '').startswith(
        "BIANCO")
    set_game_backend(backend)
    return jsonify(
        couples=formatted_couples_board,
        singles=formatted_singles_board,
        couples2=formatted_couples2_board,
        singles2=formatted_singles2_board,
        charlie=formatted_charlie_board,
        statico=formatted_statico_board,
        next_player_alfa_bravo_id=next_player_alfa_bravo_id,
        next_player_alfa_bravo_name=next_player_alfa_bravo_name,
        next_player_alfa_bravo_id2=next_player_alfa_bravo_id2,
        next_player_alfa_bravo_name2=next_player_alfa_bravo_name2,
        next_player_charlie_id=next_player_charlie_id,
        next_player_charlie_name=next_player_charlie_name,
        next_player_statico_id=backend.next_player_statico_id,  # Aggiungiamo
        next_player_statico_name=backend.next_player_statico_name,  # Aggiungiamo
        current_player_alfa=current_player_alfa,
        current_player_bravo=current_player_bravo,
        current_player_alfa2=current_player_alfa2,
        current_player_bravo2=current_player_bravo2,
        current_player_charlie=current_player_charlie,
        current_player_delta=backend.current_player_delta,  # Aggiungiamo
        current_player_echo=backend.current_player_echo,  # Aggiungiamo
        player_icon_url=url_for('static', filename='icons/Vector.svg'),
        alfa_status='Occupata' if backend.current_player_alfa else 'Libera',
        bravo_status='Occupata' if backend.current_player_bravo else 'Libera',
        alfa2_status='Occupata' if backend.current_player_alfa2 else 'Libera',
        bravo2_status='Occupata' if backend.current_player_bravo2 else 'Libera',
        charlie_status='Occupata' if backend.current_player_charlie else 'Libera',
        delta_status='Occupata' if backend.current_player_delta else 'Libera',  # Aggiungiamo
        echo_status='Occupata' if backend.current_player_echo else 'Libera',  # Aggiungiamo
        alfa_remaining=f"{int(alfa_remaining)}min" if alfa_remaining > 0 else "0min",
        bravo_remaining=f"{int(bravo_remaining)}min" if bravo_remaining > 0 else "0min",
        alfa2_remaining=f"{int(alfa2_remaining)}min" if alfa2_remaining > 0 else "0min",
        bravo2_remaining=f"{int(bravo2_remaining)}min" if bravo2_remaining > 0 else "0min",
        charlie_remaining=f"{int(charlie_remaining)}min" if charlie_remaining > 0 else "0min",
        delta_remaining=f"{int(delta_remaining)}min" if delta_remaining > 0 else "0min",  # Aggiungiamo
        echo_remaining=f"{int(echo_remaining)}min" if echo_remaining > 0 else "0min",  # Aggiungiamo
        alfa_duration=durations.get('alfa', "N/D"),
        bravo_duration=durations.get('bravo', "N/D"),
        alfa2_duration=durations.get('alfa2', "N/D"),
        bravo2_duration=durations.get('bravo2', "N/D"),
        charlie_duration=durations.get('charlie', "N/D"),
        delta_duration=durations.get('delta', "N/D"),  # Aggiungiamo
        echo_duration=durations.get('echo', "N/D"),  # Aggiungiamo
        can_stop_couple1=can_stop_couple1,
        can_stop_couple2=can_stop_couple2,
        can_stop_single1=can_stop_single1,
        can_stop_single2=can_stop_single2
    )


def get_skipped():
    backend = get_game_backend()
    return jsonify({
        'couples': [{'id': c['id']} for c in backend.skipped_couples],
        'singles': [{'id': s['id']} for s in backend.skipped_singles],
        'couples2': [{'id': c2['id']} for c2 in backend.skipped_couples2],
        'singles2': [{'id': s2['id']} for s2 in backend.skipped_singles2],
        'charlie': [{'id': p['id']} for p in backend.skipped_charlie],
        'statico': [{'id': p['id']} for p in backend.skipped_statico]
    })


def service_button_press():
    backend = get_game_backend()
    button = request.json.get('button')
    now = date.get_current_time()

    if button in ['first_start', 'second_start', 'first_start2', 'second_start2',
                  'third', 'third2',
                  'charlie_start', 'charlie_stop',  # charlie_stop verrà modificato dopo
                  'statico_start_delta', 'statico_start_echo',
                  'statico_stop_delta', 'statico_stop_echo']:

        if button == 'first_start':
            if not backend.queue_couples:
                return jsonify(success=False, error="La coda delle coppie è vuota. Non è possibile avviare il gioco.")

            backend.start_game(is_couple=True)
            set_game_backend(backend)
            return jsonify(success=True, start_time=now.isoformat(), current_player_bravo=backend.current_player_bravo,
                           current_player_alfa=backend.current_player_alfa)

        elif button == 'first_start2':  # NUOVO CASO SPECIFICO
            if not backend.queue_couples2:  # Controlla queue_couples2
                return jsonify(success=False, error="La coda Coppie 2 (Rosa) è vuota.")
            try:
                backend.start_game2(is_couple=True)  # Chiama start_game2
                set_game_backend(backend)
                return jsonify(success=True, start_time=now.isoformat(),
                               current_player_bravo2=backend.current_player_bravo2,
                               current_player_alfa2=backend.current_player_alfa2)
            except ValueError as e:
                return jsonify(success=False, error=str(e)), 400

        elif button == 'second_start':
            if not backend.queue_singles:
                return jsonify(success=False, error="La coda dei singoli è vuota. Non è possibile avviare il gioco.")
            backend.start_game(is_couple=False)
            set_game_backend(backend)
            return jsonify(success=True, start_time=now.isoformat(), current_player_alfa=backend.current_player_alfa)

        elif button == 'second_start2':
            if not backend.queue_singles2:
                return jsonify(success=False, error="La coda dei singoli è vuota. Non è possibile avviare il gioco.")
            backend.start_game2(is_couple=False)
            set_game_backend(backend)
            return jsonify(success=True, start_time=now.isoformat(), current_player_alfa2=backend.current_player_alfa2)



        elif button == 'third':
            backend.button_third_pressed()
            set_game_backend(backend)
            return jsonify(success=True)

        elif button == 'third2':
            try:
                # Chiama la funzione specifica nel backend
                backend.button_third_pressed2()
                logging.info("Metà percorso 2 (third2) attivato con successo.")
                set_game_backend(backend)
                return jsonify(success=True)
            except ValueError as e:  # Cattura l'errore se non c'è la coppia giusta
                logging.warning(f"Attivazione third2 fallita: {e}")
                return jsonify(success=False, error=str(e)), 400  # Restituisce l'errore al frontend
            except Exception as e:  # Cattura altri errori imprevisti
                logging.error(f"Errore imprevisto durante l'attivazione di third2: {e}", exc_info=True)
                return jsonify(success=False, error="Errore interno del server."), 500

        if button == 'charlie_start':
            if not backend.queue_charlie:
                logging.warning(f"Charlie start aborted: Queue empty.")
                return jsonify(success=False, error="La coda di Charlie è vuota.")
            try:
                backend.start_charlie_game()
                logging.info(f"Charlie game started for player: {backend.current_player_charlie}")
                response_data = {
                    'success': True,
                    'current_player_charlie': backend.current_player_charlie
                }
                set_game_backend(backend)
                return jsonify(response_data)
            except Exception as e:
                logging.error(f"Error during charlie_start: {e}", exc_info=True)
                response_data['error'] = f"Errore avvio Charlie: {e}"
                return None

        elif button == 'charlie_stop':
            player_info = backend.current_player_charlie
            if player_info and player_info.get('id'):
                player_id = player_info['id']
                start_time = backend.player_start_times.get(player_id)
                if start_time:
                    timer_duration_minutes = (now - start_time).total_seconds() / 60.0
                    logging.info(
                        f"Charlie stop requested for {player_id}. Timer duration: {timer_duration_minutes:.4f} min.")
                    try:
                        # Chiama record_charlie_game SOLO con la durata del timer
                        backend.record_charlie_game(timer_duration_minutes)

                        # Prepara la risposta per il frontend, includendo chi ha finito
                        response_data = {
                            'success': True,
                            'player_id': player_id,
                            'player_name': backend.get_player_name(player_id)  # Passa il nome
                        }
                        set_game_backend(backend)
                        return (jsonify(response_data))
                        # NON salvare in scoring qui, NON checkare qualifica qui
                        logging.info(f"Charlie timer recorded for {player_id}. Ready for manual input.")
                    except Exception as e:
                        logging.error(f"Error during backend.record_charlie_game: {e}", exc_info=True)
                        response_data['error'] = f"Errore registrazione timer Charlie: {e}"
                        return (jsonify(response_data))

                else:
                    logging.error(f"Charlie stop failed for {player_id}: Start time not found.")
                    # Forse è meglio chiamare comunque record_charlie_game con 0 o T_default?
                    # backend.record_charlie_game(backend.T_charlie) # Fallback?
                    response_data = {'error': f"Errore: Orario inizio non trovato per {player_id}."}
                    return (jsonify(response_data))

            else:
                logging.warning(f"Charlie stop requested but no player active.")
                response_data = {'error': "Nessun giocatore Charlie attivo da fermare."}
                return None

        # Nuovi casi per Statico DELTA e ECHO
        elif button == 'statico_start_delta':
            if not backend.queue_statico:
                return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
            if backend.current_player_delta:
                return jsonify(success=False, error="La pista DELTA è già occupata.")

            backend.start_statico_game(pista='delta')
            set_game_backend(backend)
            return jsonify(
                success=True,
                current_player_delta=backend.current_player_delta,
                current_player_echo=None
            )

        elif button == 'statico_start_echo':
            if not backend.queue_statico:
                return jsonify(success=False, error="La coda di Statico è vuota. Non è possibile avviare il gioco.")
            if backend.current_player_echo:
                return jsonify(success=False, error="La pista ECHO è già occupata.")

            backend.start_statico_game(pista='echo')
            set_game_backend(backend)
            return jsonify(
                success=True,
                current_player_delta=None,
                current_player_echo=backend.current_player_echo
            )

        elif button == 'statico_stop_delta':
            if backend.current_player_delta:
                player_id = backend.current_player_delta.get('id')
                if player_id and player_id in backend.player_start_times:
                    backend.record_statico_game(
                        (now - backend.player_start_times[player_id]).total_seconds() / 60,
                        pista='delta'
                    )
                    backend.current_player_delta = None
                    set_game_backend(backend)
                    return jsonify(success=True)
                else:
                    return jsonify(success=False,
                                   error="Errore nel recupero del tempo di inizio del giocatore Statico (DELTA).")
            return jsonify(success=False, error="Nessun giocatore Statico in pista DELTA.")

        elif button == 'statico_stop_echo':
            if backend.current_player_echo:
                player_id = backend.current_player_echo.get('id')
                if player_id and player_id in backend.player_start_times:
                    backend.record_statico_game(
                        (now - backend.player_start_times[player_id]).total_seconds() / 60,
                        pista='echo'
                    )
                    backend.current_player_echo = None
                    return jsonify(success=True)
                else:
                    return jsonify(success=False,
                                   error="Errore nel recupero del tempo di inizio del giocatore Statico (ECHO).")
            return jsonify(success=False, error="Nessun giocatore Statico in pista ECHO.")
        return None

    elif button in ['first_stop', 'second_stop', 'first_stop2', 'second_stop2']:

        try:
            if button == 'first_stop':
                control = request.json.get('control')
                if control:
                    can_stop = backend.can_stop_couple()
                    if not can_stop: return jsonify(success=False, error="Stop coppia non possibile (metà percorso?).")
                current_p = backend.current_player_couple  # La coppia che è in Bravo
                if not current_p: return jsonify(success=False, error="Nessuna coppia attiva trovata per lo stop.")
                player_id = current_p['id']
                player_type = 'couple'
                start_time = backend.player_start_times.get(player_id)

            elif button == 'second_stop':
                current_p = backend.current_player_alfa
                if not (current_p and current_p.get('id', '').startswith("BLU")):
                    return jsonify(success=False, error="Nessun singolo (BLU) in pista ALFA.")
                player_id = current_p['id']
                player_type = 'single'
                start_time = backend.player_start_times.get(player_id)

            elif button == 'first_stop2':
                can_stop = backend.can_stop_couple2()
                if not can_stop: return jsonify(success=False, error="Stop coppia 2 non possibile (metà percorso?).")
                current_p = backend.current_player_couple2
                if not current_p: return jsonify(success=False, error="Nessuna coppia 2 attiva trovata per lo stop.")
                player_id = current_p['id']
                player_type = 'couple2'  # Tipo specifico per il DB average_times
                start_time = backend.player_start_times.get(player_id)

            else: #  'second_stop2'
                current_p = backend.current_player_alfa2
                if not (current_p and current_p.get('id', '').startswith("BIANCO")):
                    return jsonify(success=False, error="Nessun singolo (BIANCO) in pista ALFA 2.")
                player_id = current_p['id']
                player_type = 'single2'  # Tipo specifico
                start_time = backend.player_start_times.get(player_id)

            # Verifica comune
            if not player_id: return jsonify(success=False, error="ID giocatore non trovato.")
            if not start_time:
                logging.error(f"Start time missing for {player_id} on {button}")
                # Cosa fare qui? Non possiamo calcolare la durata.
                # Forse forzare uno stato di errore nel frontend?
                return jsonify(success=False, error=f"Orario inizio non trovato per {player_id}.")

            player_name = backend.get_player_name(player_id)
            timer_duration_minutes = (now - start_time).total_seconds() / 60.0
            logging.info(
                f"Stop '{button}' premuto per {player_id} ({player_name}). Durata Timer Calcolata: {timer_duration_minutes:.4f} min.")

        except Exception as e:
            logging.error(f"Errore durante la preparazione dello stop per {button}: {e}", exc_info=True)
            return jsonify(success=False, error=f"Errore interno preparazione stop: {e}"), 500

        # 2. NON fare altro qui (no record, no save, no check qualifica)
        #    Restituisci i dati al frontend per il modal delle penalità

        logging.info(f"--- Button Press (Stop Prep): {button} SUCCESS ---")
        set_game_backend(backend)
        return jsonify(
            success=True,
            action="penalty_input_required",  # Segnala al frontend cosa fare
            player_id=player_id,
            player_name=player_name,
            timer_duration_minutes=timer_duration_minutes,
            player_type=player_type  # Es: 'couple', 'single', 'couple2', 'single2'
        )
    return None


def service_add_statico():
    backend = get_game_backend()
    player_id = request.json.get('id')
    name = request.json.get('name')
    if not player_id or not name:
        return jsonify(success=False, error="ID and name are required"), 400
    if player_id > 100:
        return jsonify(success=False, error="ID must be less than 100"), 400
    statico_id = f"{name.upper()} {int(player_id):03d}"
    backend.add_statico_player(statico_id, name)
    set_game_backend(backend)
    return jsonify(success=True)


def service_skip_statico_player():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        backend.skip_statico_player(player_id)
        set_game_backend(backend)
        return jsonify(
            success=True,
            next_player_statico_id=backend.next_player_statico_id,
            next_player_statico_name=backend.next_player_statico_name
        )
    return jsonify(success=False, error="Player ID is required"), 400


def service_delete_player():
    backend = get_game_backend()
    player_id = request.json.get('id')
    if player_id:
        backend.delete_player(player_id)
        set_game_backend(backend)
        return jsonify(success=True)
    return jsonify(success=False, error="Player ID is required"), 400