import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, os.path.join(cur_path, 'model_conf'))
sys.path.insert(-1, os.path.join(cur_path, 'db_utils'))
sys.path.insert(-1, os.path.join(cur_path, 'model_tuning'))

import feature_lists
import numpy as np
import pandas as pd
import datetime
from pymongo.errors import BulkWriteError, DuplicateKeyError

def latest_stat(cnx):
    cursor = cnx.cursor()
    cursor.execute('select max(oddsdate) from future_games')
    x = cursor.fetchall()
    cursor.close()
    return x

def upload_list(cnx, latest):
    cursor = cnx.cursor()        
    query = 'select statdate, teamname from basestats as gd where statdate >= "%s" order by teamname asc, statdate asc' % (latest)
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx

def aggregate_spread_ha(stat_list, tm, dt, sql_client, sa, fa):   
#    stat_list, tm, dt, sql_client, sa, fa = ha_stats, target_team, date_limit, sql, sa, 'for'
    cursor = sql_client.cursor()  
    query = 'select opponent from gamedata as gd where gd.teamname = "%s" and gd.date = "%s"' % (tm.replace('_', ' '), dt)
    cursor.execute(query)
    opp = cursor.fetchall()[0][0] 
    query = 'select location from gamedata as gd where gd.teamname = "%s" and gd.date = "%s"' % (tm.replace('_', ' '), dt)
    cursor.execute(query)
    loc = cursor.fetchall()[0][0]  
    spread_data = {'_team': tm.replace('_', ' '), '_date': dt, 'stats': {}}         
    if loc == tm.replace('_', ' '):
        ha_switch = 1
    elif loc == opp:
        ha_switch = -1        
    if sa == 'pts_scored':
        for lenth, stat in stat_list:
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.teamname = "%s" and location = gd.teamname and statdate < "%s" order by statdate desc limit %s;' % (stat[0], tm.replace('_', ' '), dt, lenth[0])
            cursor.execute(query)
            home_scale = cursor.fetchall()
            while ((None,)) in home_scale:
                home_scale.remove((None,))
            if home_scale == []:
                home_scale = [0]
            home_scale = np.mean([i for i in home_scale])   
        
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.teamname = "%s" and location = gd.opponent and statdate < "%s" order by statdate desc limit %s;' % (stat[0], tm.replace('_', ' '), dt, lenth[0])
            cursor.execute(query)
            away_scale = cursor.fetchall()
           
            while ((None,)) in away_scale:
                away_scale.remove((None,))
            if away_scale == []:
                away_scale = [0]
            away_scale = np.mean([i for i in away_scale]) 

            if away_scale == 0 or home_scale == 0:
                weighted = 0
            else:
                weighted = home_scale/away_scale
                weighted *= ha_switch
            spread_data['stats']['%s_g_HAspread_%s_%s' % (lenth[0], fa, stat[0])] = weighted
            
    elif sa == 'pts_allowed':
        for lenth, stat in stat_list:
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.opponent = "%s" and location = gd.teamname and statdate < "%s" order by statdate desc limit %s;' % (stat[0], tm.replace('_', ' '), dt, lenth[0])
            cursor.execute(query)
            home_scale = cursor.fetchall()
            while ((None,)) in home_scale:
                home_scale.remove((None,))
            if home_scale == []:
                home_scale = [0]
            home_scale = np.mean([i for i in home_scale])   
            
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.opponent = "%s" and location = gd.opponent and statdate < "%s" order by statdate desc limit %s;' % (stat[0], tm.replace('_', ' '), dt, lenth[0])
            cursor.execute(query)
            away_scale = cursor.fetchall()

            while ((None,)) in away_scale:
                away_scale.remove((None,))
            if away_scale == []:
                away_scale = [0]
            away_scale = np.mean([i for i in away_scale]) 

            if away_scale == 0 or home_scale == 0:
                weighted = 0
            else:                        
                weighted = home_scale/away_scale
                weighted *= ha_switch
            spread_data['stats']['%s_g_HAspread_%s_%s' % (lenth[0], fa, stat[0])] = weighted
    return spread_data

def aggregate_weighted_ha(stat_list, tm, dt, sql_client, sa, fa):   
#    stat_list, tm, dt, sql_client, sa, fa = ha_stats, target_team, date_limit, sql, sa, fa
    cursor = sql_client.cursor()  
    query = 'select opponent from gamedata as gd where gd.teamname = "%s" and gd.date = "%s"' % (tm.replace('_', ' '), dt)
    cursor.execute(query)
    opp = cursor.fetchall()[0][0] 
    query = 'select location from gamedata as gd where gd.teamname = "%s" and gd.date = "%s"' % (tm.replace('_', ' '), dt)
    cursor.execute(query)
    loc = cursor.fetchall()[0][0]  
    aggregated_data = {'_team': tm.replace('_', ' '), '_date': dt, '_opponent': opp, '_loc': loc, 'stats': {}}         
    if sa == 'pts_scored':
        for lenth, stat in stat_list:
            query = 'select `%s` from basestats as bs where bs.teamname = "%s" and bs.statdate = "%s"' % (stat[0], tm.replace('_', ' '), dt)
            cursor.execute(query)
            raw = cursor.fetchall()[0][0] 
            if str(raw) == 'None':
                return aggregated_data
            query = None
            if loc == tm.replace('_', ' '):
                query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.opponent = "%s" and location = gd.teamname and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            elif loc == opp:
                query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.opponent = "%s" and location = gd.opponent and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            cursor.execute(query)
            scale = cursor.fetchall()
            if len(scale) == 0:
                return aggregated_data
            while ((None,)) in scale:
                scale.remove((None,))
            scale = np.mean([i for i in scale])
            if scale == 0:
                return aggregated_data
            weighted = raw/scale
            aggregated_data['stats']['%s_g_HAweight_%s_%s' % (lenth[0], fa, stat[0])] = weighted
    elif sa == 'pts_allowed':
        for lenth, stat in stat_list:
            query = 'select `%s` from basestats as bs where bs.teamname = "%s" and bs.statdate = "%s"' % (stat[0], opp, dt)
            cursor.execute(query)
            raw = cursor.fetchall()[0][0] 
            if str(raw) == 'None':
                return aggregated_data
            query = None
            if loc == tm.replace('_', ' '):
                query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.teamname = "%s" and location = gd.teamname and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            elif loc == opp:
                query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.teamname = "%s" and location = gd.opponent and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            cursor.execute(query)
            scale = cursor.fetchall()
            if len(scale) == 0:
                return aggregated_data
            while ((None,)) in scale:
                scale.remove((None,))
            scale = np.mean([i for i in scale])
            if scale == 0:
                return aggregated_data
            weighted = raw/scale             
            aggregated_data['stats']['%s_g_HAweight_%s_%s' % (lenth[0], fa, stat[0])] = weighted
    return aggregated_data

def aggregate_weighted_team(data, stat_list, sql_client, sa, fa):
#   data, stat_list, tm, dt, sql_client, sa, fa = ha_data, tm_stats, target_team, date_limit, sql, sa, 'for'
    cursor = sql_client.cursor()  
    opp = data['_opponent']
    tm = data['_team']
    dt = data['_date']
    if sa == 'pts_scored':
        for lenth, stat in stat_list:
            query = 'select `%s` from basestats as bs where bs.teamname = "%s" and bs.statdate = "%s"' % (stat[0], tm.replace('_', ' '), dt)
            cursor.execute(query)
            raw = cursor.fetchall()[0][0] 
            if str(raw) == 'None':
                return data
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.opponent = "%s" and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            cursor.execute(query)
            scale = cursor.fetchall()
            if len(scale) == 0:
                return data
            while ((None,)) in scale:
                scale.remove((None,))
            scale = np.mean([i for i in scale])
            if scale == 0:
                return data
            weighted = raw/scale
            data['stats']['%s_g_Tweight_%s_%s' % (lenth[0], fa, stat[0])] = weighted
    elif sa == 'pts_allowed':
        for lenth, stat in stat_list:
            query = 'select `%s` from basestats as bs where bs.teamname = "%s" and bs.statdate = "%s"' % (stat[0], opp, dt)
            cursor.execute(query)
            raw = cursor.fetchall()[0][0] 
            if str(raw) == 'None':
                return data
            query = 'SELECT `%s` FROM ncaa_bb.basestats as bs join gamedata as gd on bs.statdate = gd.date and bs.teamname = gd.teamname where gd.teamname = "%s" and statdate < "%s" order by statdate desc limit %s;' % (stat[0], opp, dt, lenth[0])
            cursor.execute(query)
            scale = cursor.fetchall()
            if len(scale) == 0:
                return data
            while ((None,)) in scale:
                scale.remove((None,))
            if scale == 0:
                return data
            scale = np.mean([i for i in scale])
            weighted = raw/scale             
            data['stats']['%s_g_Tweight_%s_%s' % (lenth[0], fa, stat[0])] = weighted
    return data
    
def weighted(queue, mongo, sql, tm_stats, ha_stats, sa, fa):
#    queue, mongo, sql, tm_stats, ha_stats, sa, fa = to_add_weighted, db['weighted_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))], mysql_client, weighted_team_stats, weighted_ha_stats, sa, for_against
    latest_weighted_id = mongo.find_one(sort=[('_id', -1)])['_id']
    same_team = None
    same_tmgm = None    
    return_data = [] 
    
    duplicate_id_list = []
    duplicate_game_list = []
    for game_idx in queue:
        ha_data = None
        tm_data = None
        date_limit = game_idx[:10]
        target_team = game_idx[10:]                
        latest_weighted_id += 1
    
        if same_team != target_team:
            print('+ %s' % (target_team))
            same_team = target_team
            try:
                same_tmgm = mongo.find_one({'_team':same_team}, sort=[('_id', -1)])['_game']
            except TypeError:
                same_tmgm = 0
        same_tmgm += 1
        ha_data = aggregate_weighted_ha(ha_stats, target_team, date_limit, sql, sa, fa)
        tm_data = aggregate_weighted_team(ha_data, tm_stats, sql, sa, fa)
        if tm_data['stats'] == {}:
            print('SQL Error: %s on %s' % (target_team, date_limit))
            same_tmgm -= 1
            latest_weighted_id -= 1
            continue
        del tm_data['_loc']
        del tm_data['_opponent']
        if same_team+str(same_tmgm) in duplicate_game_list or latest_weighted_id in duplicate_id_list:
            input('duplicate metadata keys found')
        tm_data['_game'] = same_tmgm
        duplicate_game_list.append(same_team+str(same_tmgm))
        tm_data['_id'] = latest_weighted_id
        duplicate_id_list.append(latest_weighted_id)
        tm_data['_team'] = tm_data['_team'].replace(' ', '_')
        return_data.append(tm_data)
        
    try:
        mongo.insert_many(return_data)
    except BulkWriteError:
        for indy_update in return_data:
            try:
                mongo.insert_one(indy_update)
            except DuplicateKeyError:
                if indy_update['_game'] == mongo.find_one({'_id': indy_update['_id']})['_game'] and indy_update['_team'] == mongo.find_one({'_id': indy_update['_id']})['_team']:
                    mongo.update_one({'_id': indy_update['_id']}, {'$set': indy_update})
                else:
                    update_confimation = input('Mismatching meta data on update: original team = %s vs new team = %s | original game = %s vs new game = %s.  Proceed with Update?' % (mongo.find_one({'_id': indy_update['_id']})['_team'], indy_update['_team'], mongo.find_one({'_id': indy_update['_id']})['_game'], indy_update['_game']))
                    if update_confimation.upper() in ['Y', 'YES', 'YEAH']:
                        mongo.update_one({'_id': indy_update['_id']}, {'$set': indy_update})
                    else:
                        continue
   
    
def spread(queue, mongo, sql, tm_stats, ha_stats, sa, fa):
#    queue, mongo, sql, tm_stats, ha_stats, sa, fa = to_add_spread, db['hfa-spread_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))], mysql_client, weighted_team_stats, weighted_ha_stats, 'pts_scored', 'for'
    latest_weighted_id = mongo.find_one(sort=[('_id', -1)])['_id']
    same_team = None
    same_tmgm = None    
    return_data = []
    
    duplicate_id_list = []
    duplicate_game_list = []
    for game_idx in queue:
        spread_data = None
        latest_weighted_id += 1
        date_limit = game_idx[:10]
        target_team = game_idx[10:] 

        if same_team != target_team:
            print('+ %s' % (target_team))
            same_team = target_team
            try:
                same_tmgm = mongo.find_one({'_team':same_team}, sort=[('_id', -1)])['_game']
            except TypeError:
                same_tmgm = 0
        same_tmgm += 1
        date_limit = game_idx[:10]
        target_team = game_idx[10:]    
        spread_data = aggregate_spread_ha(ha_stats, target_team, date_limit, sql, sa, fa)
        if spread_data['stats'] == {}:
            print('SQL Error: %s on %s' % (target_team, date_limit))
            same_tmgm -= 1
            latest_weighted_id -= 1
            continue 
        
        if same_team+str(same_tmgm) in duplicate_game_list or latest_weighted_id in duplicate_id_list:
            input('duplicate metadata keys found')
        spread_data['_game'] = same_tmgm
        duplicate_game_list.append(same_team+str(same_tmgm))
        spread_data['_id'] = latest_weighted_id
        duplicate_id_list.append(latest_weighted_id)
        spread_data['_team'] = spread_data['_team'].replace(' ', '_')
        return_data.append(spread_data)

    try:
        mongo.insert_many(return_data)
    except BulkWriteError:
        for indy_update in return_data:
            try:
                mongo.insert_one(indy_update)
            except DuplicateKeyError:
                if indy_update['_game'] == mongo.find_one({'_id': indy_update['_id']})['_game'] and indy_update['_team'] == mongo.find_one({'_id': indy_update['_id']})['_team']:
                    mongo.update_one({'_id': indy_update['_id']}, {'$set': indy_update})
                else:
                    update_confimation = input('Mismatching meta data on update: original team = %s vs new team = %s | original game = %s vs new game = %s.  Proceed with Update?' % (mongo.find_one({'_id': indy_update['_id']})['_team'], indy_update['_team'], mongo.find_one({'_id': indy_update['_id']})['_game'], indy_update['_game']))
                    if update_confimation.upper() in ['Y', 'YES', 'YEAH']:
                        mongo.update_one({'_id': indy_update['_id']}, {'$set': indy_update})
                    else:
                        continue
  
    
    
def insert(od, sa, client, mysql_client):
#    od, sa, client, mysql_client = 'possessions', 'pts_scored', mongodb_client, mysql_client()    
    if od == 'offensive_stats':
        for_against = 'for'
    elif od == 'defensive_stats':
        for_against = 'allow'
    elif od in ['possessions', 'target']:
        if sa == 'pts_scored':
            for_against = 'for'
        elif sa == 'pts_allowed':
            for_against = 'allow'
    
    db = client['ncaa_bb']
    
#    try:
#        validation_season = db['weighted_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].find_one({'_date': '2017-11-12'}, sort=[('_id', 1)])['_id']
#        db['weighted_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].delete_many({'_id': {'$gte': validation_season}})
#        return
#    except TypeError:
#        return
#
#    try:
#        validation_season = db['hfa-spread_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].find_one({'_date': '2017-11-10'}, sort=[('_id', 1)])['_id']
#        db['hfa-spread_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].delete_many({'_id': {'$gte': validation_season}})
#        return
#    except TypeError:
#        return
    
    try:
        latest_weighted = db['weighted_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].find_one(sort=[('_id', -1)])['_date']
    except TypeError:
        print('***Empty weighted %s %s db found. You can bootstrap the historical data from GitHub.' % (sa, od.replace('_', '-')))
        latest_weighted = "2009-01-01"
    try:
        latest_spread = db['hfa-spread_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))].find_one(sort=[('_id', -1)])['_date']
    except TypeError:
        print('***Empty homefield advantage %s %s db found.  You can bootstrap the historical data from GitHub.' % (sa, od.replace('_', '-')))
        latest_spread = "2009-01-01"   
        
    statlist = feature_lists.stats[sa][od]
    weighted_stats = []
    hfaspread_stats = []
    for stat in statlist:
        try:
            if stat.split('_game_avg_')[1] not in weighted_stats:
                weighted_stats.append(stat.split('_game_avg_')[1])
        except IndexError:
            n, s = stat.split('_game_ha_spread_')
            if stat not in hfaspread_stats:
                hfaspread_stats.append((n, s))
    stat = None
    weighted_ha_stats = []
    weighted_team_stats = []
    for stat in weighted_stats:
        try:
            n, s = stat.split('_game_ha_weighted_')
            if (n.split('_'), s.split('_')) not in weighted_ha_stats:
                weighted_ha_stats.append((n.split('_'), s.split('_')))
        except ValueError:
            n, s = stat.split('_game_team_weighted_')
            if (n.split('_'), s.split('_')) not in weighted_team_stats:
                weighted_team_stats.append((n.split('_'), s.split('_')))
    n = None
    s = None
    stat = None
        
    to_add_weighted = upload_list(mysql_client, latest_weighted)
    to_add_spread = upload_list(mysql_client, latest_spread)
    
    weighted(to_add_weighted, db['weighted_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))], mysql_client, weighted_team_stats, weighted_ha_stats, sa, for_against)
    print('------------- completed uploading weighted %s %s-stats ---------------' %(sa, od))
    
    spread(to_add_spread, db['hfa-spread_%s_%s'% (sa.replace('_', '-'), od.replace('_', '-'))], mysql_client, weighted_team_stats, weighted_ha_stats, 'pts_scored', 'for')
    print('------------- completed uploading hfa spread %s %s-stats ---------------' %(sa, od))

