def format_list(player_list,player_names):
    final_list = []
    for pos, player_id, time_est in player_list:
        final_list.append({
            'id': player_id,
            'name': player_names.get(player_id),
            'estimated_time': time_est
        })
    return final_list