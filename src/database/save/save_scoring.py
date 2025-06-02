from ...utils.model import get_game_backend,set_game_backend

def update_score_formatted(backend,player_id,score):
    for list_tuple_score in [backend.couple_history_total,backend.couple_history_total2,backend.single_history,backend.single_history2]:
        for tuple_score in list_tuple_score:
            if tuple_score[0] == player_id:
                indice = list_tuple_score.index(tuple_score)
                list_tuple_score[indice] = (player_id, score)
                set_game_backend(backend)


def refresh_scoring(scoring_list,backend,cursor):
    for scoring in scoring_list:
        if scoring[1]:
            for player_id, score in scoring[1]:
                cursor.execute(
                    "INSERT INTO scoring (player_type, player_id, player_name, score) VALUES (?, ?, ?, ?)",
                    (scoring[0], player_id, backend.get_player_name(player_id), score)
                )