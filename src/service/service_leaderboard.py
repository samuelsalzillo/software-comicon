"""
Recupera i primi 3 giocatori qualificati per tipo (couple, single, charlie)
basandosi sul tempo più basso registrato nella tabella qualified_players.
(Assume che la colonna player_id contenga l'ID CORTO: "COLORE NNN")
"""
import logging
import os

from ..repository import get_qualified_players_repository
from ..utils.date import format_time_into_mmss, converti_float_mmss_in_secondi_totali
from ..database.select.qualified_players import find_by_type_id_player, find_by_id_player
from ..database.save.save_qualified_players import update_score_formatted_and_score_minutes
from flask import jsonify
from .service_treasure_hunt import get_all_treasure_hunt
from ..database.save.save_scoring import update_score_formatted
from ..utils.model import get_game_backend


def get_top3_leaderboard():
    """
    Get top 3 qualified players for each type using repository pattern.
    """
    top3_data = {
        'couples': [],
        'singles': [],
        'charlie': []
    }

    player_types = ['couple', 'single', 'charlie']
    qualified_repo = get_qualified_players_repository()
    treasure_hunt_active = os.environ.get("TREASURE_HUNT_ACTIVE")

    try:
        for p_type in player_types:
            logging.debug(f"Querying top 3 for type: {p_type}")

            # Use repository to fetch qualified players
            qualified_players = qualified_repo.find_qualified_by_type(p_type, limit=3)

            # Filter by treasure hunt if active (for couple/single)
            if treasure_hunt_active and p_type in ('couple', 'single'):
                qualified_players = [
                    p for p in qualified_players
                    if p.get('treasure_hunt_updated') is not None
                    and p.get('qualification_reason') != 'Non qualificato'
                ]
            else:
                qualified_players = [
                    p for p in qualified_players
                    if p.get('qualification_reason') != 'Non qualificato'
                ]

            logging.debug(f"Found {len(qualified_players)} results for {p_type}")

            rank = 1
            for player in qualified_players:
                player_entry = {
                    "rank": rank,
                    "id": player['player_id'],
                    "name": f"{player['first_name']} {player['last_name']}",
                    "score": player['score_formatted']
                }

                # Add to correct list
                if p_type in top3_data:
                    top3_data[p_type].append(player_entry)
                elif p_type + 's' in top3_data:
                    top3_data[p_type + 's'].append(player_entry)

                rank += 1

        return jsonify(top3_data)

    except Exception as e:
        logging.error(f"Error in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500

def sync_new_date():
    metadata = get_all_treasure_hunt()
    backend = get_game_backend()
    player_types = ['couple', 'single', 'charlie']  # Tipi da cercare
    try:
        for data in metadata:
            for player_type in player_types:
                row = find_by_type_id_player(player_type,data.id_player)
                if row:
                    player_id, player_name, score = row
                    if not find_by_id_player(player_id):
                        differenza_in_secondi = (data.timestamp_fine - data.timestamp_inizio).total_seconds()
                        if data.qr_code_founded != data.qr_code:
                            differenza_in_secondi = differenza_in_secondi + 216000 # todo PER IL CALCOLO DEL MIGLIORE AGGIUNGO 60 ORE
                        score_minutes = (differenza_in_secondi + converti_float_mmss_in_secondi_totali(score)) / 60
                        score_formatted = format_time_into_mmss(score_minutes)
                        if data.qr_code_founded != data.qr_code:
                            is_qualified, reason = False,"Non qualificato"
                        else:
                            is_qualified, reason=  backend.check_qualification(score_minutes,player_type)
                        update_score_formatted_and_score_minutes(player_id,player_name,player_type,data,score_formatted,score_minutes,reason if is_qualified else "Non qualificato")
                        update_score_formatted(backend,player_id,score_minutes)
                    logging.debug(f"Found {len(row)} and update results for {player_type}")
        return jsonify(error="Operazione completata con successo"), 200


    except Exception as e:
        logging.error(f"Errore generico in /leaderboard/top3: {e}", exc_info=True)
        return jsonify(error="Errore interno del server"), 500
