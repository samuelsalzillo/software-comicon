from ..database.select.scoring import get_scoring_by_player_id

def format_list(player_list,player_names):
    final_list = []
    for pos, player_id, time_est in player_list:
        final_list.append({
            'id': player_id,
            'name': player_names.get(player_id),
            'estimated_time': time_est
        })
    return final_list

def get_date_for_player_id(player_id):
    return get_scoring_by_player_id(player_id)