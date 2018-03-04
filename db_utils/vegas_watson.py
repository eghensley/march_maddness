import numpy as np
import pandas as pd
import pull_data
import update_dbs
import bb_odds

def rolling_vegas(result):
    odds = pull_data.pull_odds_data(update_dbs.mysql_client())
    teams = bb_odds.teamnames
    aou_data = {}
    atl_data = {}
    
    aou_streak = {}
    atl_streak = {}
    vegas_data_line = {}
    vegas_data_ou = {}
    for team in teams:
        aou_data[team] = []
        atl_data[team] = []
        aou_streak[team] = 0
        atl_streak[team] = 0
    for date,fav,dog,line,overunder,favscore,dogscore, homeaway in np.array(odds[['date','fav','dog','line','overunder','fav-score','dog-score', 'ha']]): 
        if len(aou_data[fav]) > 0 and len(atl_data[fav]) > 0:
            vegas_data_line[str(date)+fav.replace(' ','_')] = {}
            vegas_data_ou[str(date)+fav.replace(' ','_')] = {}
            for n_games in [3,5,10,15,30,50]:
                vegas_data_ou[str(date)+fav.replace(' ','_')]['%s_game_avg'%(n_games)] = np.mean(aou_data[fav][-n_games:])
                if n_games in [10, 50]:
                    vegas_data_line[str(date)+fav.replace(' ','_')]['%s_game_avg'%(n_games)] = np.mean(atl_data[fav][-n_games:])                
            if homeaway == 0:
                vegas_data_line[str(date)+fav.replace(' ','_')]['ha'] = 1       
            elif homeaway == 1:
                vegas_data_line[str(date)+fav.replace(' ','_')]['ha'] = 0  
            vegas_data_ou[str(date)+fav.replace(' ','_')]['streak'] = aou_streak[fav]   
            vegas_data_line[str(date)+fav.replace(' ','_')]['streak'] = atl_streak[fav]   
            if favscore+dogscore > overunder:
                vegas_data_ou[str(date)+fav.replace(' ','_')]['result'] = 1
            else:
                vegas_data_ou[str(date)+fav.replace(' ','_')]['result'] = -1
            if favscore + line > dogscore:
                vegas_data_line[str(date)+fav.replace(' ','_')]['result'] = 1
            else:
                vegas_data_line[str(date)+fav.replace(' ','_')]['result'] = -1
                
        if len(aou_data[dog]) > 0 and len(atl_data[dog]) > 0:
            vegas_data_line[str(date)+dog.replace(' ','_')] = {}
            vegas_data_ou[str(date)+dog.replace(' ','_')] = {}
            for n_games in [3,5,10,15,30,50]:
                vegas_data_ou[str(date)+dog.replace(' ','_')]['%s_game_avg'%(n_games)] = np.mean(aou_data[dog][-n_games:])
                if n_games in [10, 50]:
                    vegas_data_line[str(date)+dog.replace(' ','_')]['%s_game_avg'%(n_games)] = np.mean(atl_data[dog][-n_games:])                
            if homeaway == 0:
                vegas_data_line[str(date)+dog.replace(' ','_')]['ha'] = 0       
            elif homeaway == 1:
                vegas_data_line[str(date)+dog.replace(' ','_')]['ha'] = 1  
            vegas_data_ou[str(date)+dog.replace(' ','_')]['streak'] = aou_streak[dog]   
            vegas_data_line[str(date)+dog.replace(' ','_')]['streak'] = atl_streak[dog]   
            if favscore+dogscore > overunder:
                vegas_data_ou[str(date)+dog.replace(' ','_')]['result'] = 1
            else:
                vegas_data_ou[str(date)+dog.replace(' ','_')]['result'] = -1
            if favscore + line > dogscore:
                vegas_data_line[str(date)+dog.replace(' ','_')]['result'] = -1
            else:
                vegas_data_line[str(date)+dog.replace(' ','_')]['result'] = 1
                
        if dogscore+favscore < overunder:
            aou_data[fav].append(-1)
            aou_data[dog].append(-1)
            if aou_streak[fav] > 0:
                aou_streak[fav] = -1
            else:
                aou_streak[fav] -= 1
            if aou_streak[dog] > 0:
                aou_streak[dog] = -1
            else:
                aou_streak[dog] -= 1            
        elif dogscore+favscore > overunder:
            aou_data[fav].append(1)
            aou_data[dog].append(1)
            if aou_streak[fav] < 0:
                aou_streak[fav] = 1
            else:
                aou_streak[fav] += 1
            if aou_streak[dog] < 0:
                aou_streak[dog] = 1
            else:
                aou_streak[dog] += 1     
        if (favscore-dogscore) + line > 0:
            atl_data[fav].append(1)
            atl_data[dog].append(-1)
            if atl_streak[fav] < 0:
                atl_streak[fav] = 1
            else:
                atl_streak[fav] += 1
            if atl_streak[dog] > 0:
                atl_streak[dog] = -1
            else:
                atl_streak[dog] -= 1
        elif (favscore-dogscore) + line < 0:
            atl_data[fav].append(-1)
            atl_data[dog].append(1)  
            if atl_streak[dog] < 0:
                atl_streak[dog] = 1
            else:
                atl_streak[dog] += 1  
            if atl_streak[fav] > 0:
                atl_streak[fav] = -1
            else:
                atl_streak[fav] -= 1
        for source in (atl_data, aou_data):
            for tm in (fav, dog):
                if len(source[tm]) > 50:
                    source[tm] = source[tm][-50:]
    
    if result == 'line':    
        vegas_data_line = pd.DataFrame.from_dict(vegas_data_line)
        vegas_data_line = vegas_data_line.T
        return vegas_data_line
    
    if result == 'ou':    
        vegas_data_ou = pd.DataFrame.from_dict(vegas_data_ou)
        vegas_data_ou = vegas_data_ou.T
        return vegas_data_ou
