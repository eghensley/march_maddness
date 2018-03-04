import numpy as np
import pandas as pd
import mysql.connector 
import feature_lists
from weighted_stats import pull_index
from datetime import datetime
import mongodb_weighted_stat_insert
import bb_odds


def elo(feature, parameters, cnx):
#    feature, parameters, cnx=each, features[each], mysql_client
    teams = bb_odds.teamnames
    cursor = cnx.cursor()
    query = "select oddsdate, favorite, `"+feature+"`, homeaway from oddsdata as od join basestats as bs on od.oddsdate = bs.statdate and od.favorite = bs.teamname"
    cursor.execute(query)
    names = ['date', 'fav', 'fav_factor', 'ha']
    fav_data = pd.DataFrame(cursor.fetchall(), columns = names)
    idlist = []
    for date, team, factor, ha in np.array(fav_data):
        idlist.append(str(date)+team.replace(' ', '_'))
    fav_data['idx'] = idlist
    fav_data = fav_data.set_index('idx')
    fav_data = fav_data[['date', 'fav', 'fav_factor', 'ha']]
    
    query = "select oddsdate, favorite, underdog, `"+feature+"` from oddsdata as od join basestats as bs on od.oddsdate = bs.statdate and od.underdog = bs.teamname"
    cursor.execute(query)
    names = ['date', 'fav', 'dog', 'dog_factor']
    dog_data = pd.DataFrame(cursor.fetchall(), columns = names)
    idlist = []
    for date, team, team2, factor in np.array(dog_data):
        idlist.append(str(date)+team.replace(' ', '_'))
    dog_data['idx'] = idlist
    dog_data = dog_data.set_index('idx')
    dog_data = dog_data[['dog', 'dog_factor']]
    data = fav_data.join(dog_data, how = 'inner')
    data = data.sort_values('date')

    cursor.close()
    hf, pwr, shrink, adj = parameters
    fordict = {}
    for team in teams:
        fordict[team] = 0
    againstdict = {}
    for team in teams:
        againstdict[team] = 0
    season = np.array(data['date'])[0].year

    elo_data = {}
    proceed = True
    for date, t1, s1, loc, t2, s2 in np.array(data):
        s1_exp = None
        s2_exp = None
        s1_error = None
        s2_error = None
        if not (str(date) == "2017-01-27" and "WI-Milwkee" in [t1, t2]):
            if proceed:
                if date.month == 11 and date.year > season:
                    fordictmean = np.mean(list(fordict.values()))
                    againstdictmean = np.mean(list(againstdict.values()))
                    for key in fordict.keys():
                        fordict[key] = fordict[key] + (fordictmean - fordict[key])*adj
                    for key in againstdict.keys():
                        againstdict[key] = againstdict[key] + (againstdictmean - againstdict[key])*adj
                    season += 1
                if loc == 1:
                     loc = -1
                elif loc == 0:
                     loc = 1
                if s1 == s1 and s2 == s2:
                    if fordict[t1] != 0 and fordict[t2] != 0 and againstdict[t1] != 0 and againstdict[t2] != 0:
                        s1_exp = (fordict[t1]+againstdict[t2])/2 + (loc * hf)
                        s2_exp = (fordict[t2]+againstdict[t1])/2 - (loc * hf)                 
                        s1_error = (s1 - s1_exp)/s1_exp
                        s2_error = (s2 - s2_exp)/s2_exp
        
                        elo_data[str(date)+t1.replace(' ', '_')] = {'expected_%s_offense' % (feature): s1_exp, 'pregame_%s_offense' % (feature) : fordict[t1], 'expected_%s_defense' % (feature): s2_exp, 'pregame_%s_defense' % (feature) : againstdict[t1]} 
                        elo_data[str(date)+t2.replace(' ', '_')] = {'expected_%s_offense' % (feature): s2_exp, 'pregame_%s_offense' % (feature) : fordict[t2], 'expected_%s_defense' % (feature): s1_exp, 'pregame_%s_defense' % (feature) : againstdict[t2]} 
        
                        if fordict[t1] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink != fordict[t1] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink:
                            proceed = False
                        if againstdict[t2] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink != againstdict[t2] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink:
                            proceed = False
                        if fordict[t2] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink != fordict[t2] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink:
                            proceed = False
                        if againstdict[t1] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink != againstdict[t1] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink:
                            proceed = False        
                        fordict[t1] = fordict[t1] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink
                        againstdict[t2] = againstdict[t2] + ((((1 + s1_error)**pwr) -1) * s1_exp)/shrink
                        fordict[t2] = fordict[t2] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink
                        againstdict[t1] = againstdict[t1] + ((((1 + s2_error)**pwr) -1) * s2_exp)/shrink 
                    else:
                        if fordict[t1] == 0:
                            fordict[t1] = s1
                        if fordict[t2] == 0:
                            fordict[t2] = s2
                        if againstdict[t1] == 0:
                            againstdict[t1] = s2
                        if againstdict[t2] == 0:
                            againstdict[t1] = s1
    return elo_data



def update(client, mysql_client):
#   client, mysql_client = mongodb_client, mysql_client()
    db = client['ncaa_bb']
        
    progress = 0
    
    try:
        latest_elo = db.elo_four_features.find_one(sort=[('_id', -1)])['_date']
    except TypeError:
        latest_elo = "2009-01-01"
        
    latest_elo = "2018-02-20" 
    elo_stats = {}
    for teamname,allowdate in np.array(pull_index()):
        if allowdate > datetime.strptime(latest_elo, '%Y-%m-%d').date():
            elo_stats[str(allowdate)+teamname.replace(' ', '_')] = {'_id': progress, '_date' : str(allowdate), '_team' : teamname, 'stats':{'offensive_stats':{}, 'defensive_stats':{}, 'pts_scored':{'target':{}, 'possessions':{}}, 'pts_allowed':{'target':{}, 'possessions':{}}}}
        progress += 1
    
    
    if datetime.strptime(latest_elo, '%Y-%m-%d').date() <= mongodb_weighted_stat_insert.latest_stat(mysql_client)[0][0]:
        for each in feature_lists.elo:
            print('Calculating %s Elo Rankings...' % (each))
            elo_data = elo(each, feature_lists.elo[each], mysql_client)
            
            for game in elo_data:
                if game in elo_stats.keys():
                    elo_stats[game]['stats']['offensive_stats']['expected_%s' % (each)] = elo_data[game]['expected_%s_offense' % (each)]
                    elo_stats[game]['stats']['offensive_stats']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_offense' % (each)]
                    elo_stats[game]['stats']['defensive_stats']['expected_%s' % (each)] = elo_data[game]['expected_%s_defense' % (each)]
                    elo_stats[game]['stats']['defensive_stats']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_defense' % (each)]
               
            elo_data = None
            print('...Completed %s Elo Rankings' % (each))
        for each in feature_lists.target:
            print('Calculating %s Elo Rankings...' % (each))
            if each == 'ppp':
                pull_key = 'points-per-game`/`possessions-per-game'
            elif each == 'pts_pg':
                pull_key = 'points-per-game'
            elo_data = elo(pull_key, feature_lists.target[each], mysql_client)
            
            for game in elo_data:
                if game in elo_stats.keys():
                    elo_stats[game]['stats']['pts_scored']['target']['expected_%s' % (each)] = elo_data[game]['expected_%s_offense' % (pull_key)]
                    elo_stats[game]['stats']['pts_scored']['target']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_offense' % (pull_key)]
                    elo_stats[game]['stats']['pts_allowed']['target']['expected_%s' % (each)] = elo_data[game]['expected_%s_defense' % (pull_key)]
                    elo_stats[game]['stats']['pts_allowed']['target']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_defense' % (pull_key)]
 
            pull_key = None  
            elo_data = None
            print('...Completed %s Elo Rankings' % (each))

        for each in feature_lists.possessions:
            print('Calculating %s Elo Rankings...' % (each))
            elo_data = elo('possessions-per-game', feature_lists.possessions[each], mysql_client)
            
            for game in elo_data:
                if game in elo_stats.keys():
                    elo_stats[game]['stats']['pts_scored']['possessions']['expected_%s' % (each)] = elo_data[game]['expected_%s_offense' % ('possessions-per-game')]
                    elo_stats[game]['stats']['pts_scored']['possessions']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_offense' % ('possessions-per-game')]
                    elo_stats[game]['stats']['pts_allowed']['possessions']['expected_%s' % (each)] = elo_data[game]['expected_%s_defense' % ('possessions-per-game')]
                    elo_stats[game]['stats']['pts_allowed']['possessions']['pregame_%s' % (each)] = elo_data[game]['pregame_%s_defense' % ('possessions-per-game')]
               
            elo_data = None
            print('...Completed %s Elo Rankings' % (each))
            
        print('Loading Elo Data')
        elo_stats = [elo_stats[key] for key in elo_stats.keys()]
        update_data = []
        for each in elo_stats:
            if each['stats']['defensive_stats'] != {}:
                update_data.append(each)
        db.elo_four_features.insert_many(update_data)
        print('Elo Data Updated')
        mysql_client.close()
        
