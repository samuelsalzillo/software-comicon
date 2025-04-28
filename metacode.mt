len_giallo len di giallo
current_blu posizione giocatore analizzato
N_giallo  (numero di gialli prima del blu analizzato) 


# CALCOLO DI N_GIALLO2 RELATIVAMENTE AL BLU analizzato
per ogni blu in coda
    se current_blu <= len_giallo:
        N_giallo = current_blu

    invece:
        n_giallo = len_giallo


# TEMPO DI ATTESA DEL BLU analizzato
min_att = DT_MID * N_GIALLO + DT_SINGLE * (current_BLU - 1)



#CALCOLO ATTESA GIOCATORE GIALLO

len_giallo (len dei gialli)
len_blu (len dei blu)
current_giallo ()
dt_total(tempo medio totale esecuzione giallo)
dt_mid (mezzo tempo giallo, tempo di sblocco del tasterino)
dt_single (tempo medio totale esecuzione blu)
min_att (min di attesa)

SE current_giallo < len_blu:

    SE dt_total<= (dt_single + dt_mid):
        min_att = dt_single * (current_giallo -1) + dt_mid * (current_giallo -1)

    INVECE:
        min_att = dt_total* (current_giallo -1)

INVECE:
    SE dt_total<= (dt_single + dt_mid):
        min_att = dt_single * len_blu + dt_mid * len_blu + dt_total* (current_giallo - len_blu -1)

    INVECE:
        min_att = dt_total* (current_giallo-1)