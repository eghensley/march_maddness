import pandas as pd
import numpy as np

def latest_team(cnx, team):
    cursor = cnx.cursor()
    query = 'SELECT max(date) FROM ncaa_bb.gamedata where teamname = "%s";' % (team)
    cursor.execute(query)
    update = cursor.fetchall()
    cursor = cnx.cursor()    
    return update

def future_idx(cnx):
    cursor = cnx.cursor()        
    query = 'select date, teamname from gamedata as gd join future_games as fg on gd.date = fg.oddsdate and (gd.teamname = fg.favorite or gd.teamname = fg.underdog)'
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx

def update_idx(cnx, db):
    cursor = cnx.cursor()
    query = "SELECT max(date) FROM ncaa_bb.%s;" % (db)
    cursor.execute(query)
    update = cursor.fetchall()
    cursor = cnx.cursor()
    if str(update[0][0]) == 'None':
        update = "2017-11-01"
    else:
        update = str(update[0][0])
    query = 'select date, teamname from gamedata where date >= "%s"' % (update)
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx

def pull_possessions(od, cnx): 
    print('Loading Possession Data')
    if od == 'pts_scored':
        selector = ['favorite', 'underdog']
    elif od == 'pts_allowed':
        selector = ['underdog', 'favorite']

    cursor = cnx.cursor()
    query = "select oddsdate, favorite, `possessions-per-game` from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[0])
    labels = ["oddsdate", "favorite","possessions"]
    cursor.execute(query)
    favdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(favdata):
        favid.append(str(date)+name.replace(' ','_'))
    favdata['idx'] = favid
    favdata = favdata.set_index('idx')
    favdata = favdata['possessions']
    query = "select oddsdate, underdog,`possessions-per-game` from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[1])
    labels = ["oddsdate", "underdog","possessions"]
    cursor.execute(query)
    dogdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(dogdata):
        favid.append(str(date)+name.replace(' ','_'))
    dogdata['idx'] = favid
    dogdata = dogdata.set_index('idx')
    dogdata = dogdata['possessions']
    data = favdata.append(dogdata)
    print('...Possession Data Loaded')
    
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data

def pull_wl(cnx):
    cursor = cnx.cursor()
    query = 'select gd.teamname, date, bs1.`points-per-game` - bs2.`points-per-game` from gamedata as gd join basestats as bs1 on bs1.teamname = gd.teamname and bs1.statdate = gd.date join basestats as bs2 on bs2.teamname = gd.opponent and bs2.statdate = gd.date'
    cursor.execute(query)
    gamedata = pd.DataFrame(cursor.fetchall() , columns = ['name', 'date', 'result'])
    idx = []
    result = []
    
    for n, d ,r in np.array(gamedata):
        if r > 0:
            result.append(1)
            idx.append(str(d)+n.replace(' ', '_'))
        elif r <0:
            result.append(0)
            idx.append(str(d)+n.replace(' ', '_'))
    resultdata = pd.DataFrame()
    resultdata['idx'] = idx
    resultdata['outcome'] = result
    resultdata = resultdata.set_index('idx')
    return resultdata

def ou_wl(cnx):
    cursor = cnx.cursor()
    query = 'select oddsdate, favorite, underdog, overunder, favscore, dogscore from oddsdata'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['date', 'fav', 'dog', 'ou', 'fav-score', 'dog-score'])
    idx = []
    result = []
    
    result_df = pd.DataFrame()
    for d,f,dog,l, fs, ds in np.array(oddsdata):
        if fs + ds > l:
            idx.append(str(d)+f.replace(' ', '_'))
            idx.append(str(d)+dog.replace(' ', '_'))
            result.append(1)
            result.append(1)
        elif fs + ds < l:
            idx.append(str(d)+f.replace(' ', '_'))
            idx.append(str(d)+dog.replace(' ', '_'))
            result.append(0)
            result.append(0)
            
    result_df['idx'] = idx
    result_df['ou'] = result
    
    result_df = result_df.set_index('idx')
    return result_df

def line_wl(cnx):
    cursor = cnx.cursor()
    query = 'select oddsdate, favorite, underdog, line, favscore, dogscore from oddsdata'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['date', 'fav', 'dog', 'line', 'fav-score', 'dog-score'])
    idx = []
    result = []
    
    result_df = pd.DataFrame()
    for d,f,dog,l, fs, ds in np.array(oddsdata):
        if fs + l > ds:
            idx.append(str(d)+f.replace(' ', '_'))
            idx.append(str(d)+dog.replace(' ', '_'))
            result.append(1)
            result.append(0)
        elif fs + l < ds:
            idx.append(str(d)+f.replace(' ', '_'))
            idx.append(str(d)+dog.replace(' ', '_'))
            result.append(0)
            result.append(1)
            
    result_df['idx'] = idx
    result_df['line'] = result
    
    result_df = result_df.set_index('idx')
    return result_df

def line_preds(cnx):
    cursor = cnx.cursor()
    query = 'select * from line_preds'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['teamname', 'date', 'pca_line', 'tsvd_line', 'lasso_line', 'lightgbm_line', 'ridge_line'])
    idx = []
    for d,f in np.array(oddsdata[['date', 'teamname']]):
        idx.append(str(d)+f.replace(' ', '_'))
    oddsdata['idx'] = idx
    oddsdata = oddsdata.set_index('idx')
    oddsdata = oddsdata[['pca_line', 'tsvd_line', 'lasso_line', 'lightgbm_line', 'ridge_line']]
    return oddsdata

def ou_preds(cnx):
    cursor = cnx.cursor()
    query = 'select * from ou_preds'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['teamname', 'date', 'pca_ou', 'tsvd_ou', 'lasso_ou', 'lightgbm_ou', 'ridge_ou'])
    idx = []
    for d,f in np.array(oddsdata[['date', 'teamname']]):
        idx.append(str(d)+f.replace(' ', '_'))
    oddsdata['idx'] = idx
    oddsdata = oddsdata.set_index('idx')
    oddsdata = oddsdata[['pca_ou', 'tsvd_ou', 'lasso_ou', 'lightgbm_ou', 'ridge_ou']]
    return oddsdata
    
def pull_odds_data(cnx):
    cursor = cnx.cursor()
    query = 'select * from oddsdata'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['date', 'fav', 'dog', 'line', 'line-juice', 'overunder', 'ou-juice', 'fav-ml', 'dog-ml', 'fav-score', 'dog-score', 'ha'])
    t1idx = []
    t2idx = []
    for d,f,dog,l,lj, ou, ouj, fml, dml, fs, ds, ha in np.array(oddsdata):
        t1idx.append(str(d)+f.replace(' ', '_'))
        t2idx.append(str(d)+dog.replace(' ', '_'))
    oddsdata['fav_idx'] = t1idx
    oddsdata['dog_idx'] = t2idx
    return oddsdata

def pull_days_rest(cnx):
    cursor = cnx.cursor()
    query = 'SELECT teamname, date, datediff(date, (select max(date) from gamedata as gd1 where gd1.teamname = gd.teamname and gd1.date < gd.date))  FROM ncaa_bb.gamedata as gd;'
    cursor.execute(query)
    oddsdata = pd.DataFrame(cursor.fetchall() , columns = ['name', 'date', 'rest'])
    idx = []
    for n,d,r in np.array(oddsdata):
        idx.append(str(d)+n.replace(' ', '_'))
    oddsdata['idx'] = idx
    oddsdata = oddsdata.set_index('idx')
    oddsdata['rest'] = oddsdata.rest.apply(lambda x: 10 if x > 10 else x)
    oddsdata = oddsdata['rest']
    return oddsdata
    
def pull_train_index(cnx):
    cursor = cnx.cursor()
    query = 'select date, teamname from gamedata where date < "2017-11-1"'
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx 

def pull_validation_index(cnx):
    cursor = cnx.cursor()
    query = 'select date, teamname from gamedata where date > "2017-11-1" and date <= "2018-02-27"'
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx 

def pull_new_index(cnx):
    cursor = cnx.cursor()
    query = 'select date, teamname from gamedata where date > "2018-02-27"'
    cursor.execute(query)
    indexdata = pd.DataFrame(cursor.fetchall(), columns = ['date', 'name'])
    idx = []
    for d,n in np.array(indexdata):
        idx.append(str(d)+n.replace(' ','_'))
    return idx 
   
def score(cnx):
    off_data = points(cnx, 'offense')
    off_poss = pace(cnx, 'offense')
    off_data = off_data.join(off_poss, how = 'inner')
    off_data = off_data.rename(columns = {i:'+'+i for i in list(off_data)})
    def_data = points(cnx, 'defense')
    def_poss = pace(cnx, 'defense')
    def_data = def_data.join(def_poss, how = 'inner')
    def_data = def_data.rename(columns = {i:'-'+i for i in list(def_data)})
    del def_data['-pts']
    def_data *= -1
    cursor = cnx.cursor()
    query = 'SELECT * from gamedata;'
    cursor.execute(query)
    data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'opponent', 'location'])
    idx_switch = {}
    for t,d,o,l in np.array(data):
        idx_switch[str(d)+t.replace(' ', '_')] = str(d)+o.replace(' ', '_')
    idx = []
    for idxx in def_data.index:
        idx.append(idx_switch[idxx])
    def_data['idx'] = idx
    def_data = def_data.set_index('idx')
    data = def_data.join(off_data) 
    
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data

def share(cnx):
    off_data = points(cnx, 'offense')
    off_poss = pace(cnx, 'offense')
    off_data = off_data.join(off_poss, how = 'inner')
    off_data = off_data.rename(columns = {i:'+'+i for i in list(off_data)})
    def_data = points(cnx, 'defense')
    def_poss = pace(cnx, 'defense')
    def_data = def_data.join(def_poss, how = 'inner')
    off_pts_allowed = off_data['+pts']
    def_data = def_data.join(off_pts_allowed, how = 'inner')
    def_data = def_data.rename(columns = {i:'-'+i for i in list(def_data)})
    del def_data['-pts']    

    def_data *= -1
    cursor = cnx.cursor()
    query = 'SELECT * from gamedata;'
    cursor.execute(query)
    data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'opponent', 'location'])
    idx_switch = {}
    for t,d,o,l in np.array(data):
        idx_switch[str(d)+t.replace(' ', '_')] = str(d)+o.replace(' ', '_')
    idx = []
    for idxx in def_data.index:
        idx.append(idx_switch[idxx])
    def_data['idx'] = idx
    def_data = def_data.set_index('idx')
    data = def_data.join(off_data) 
    
    data['share'] = data['+pts']/(data['+pts'] - data['-+pts'])
    del data['+pts']
    del data['-+pts']
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data

def line(cnx):
    import vegas_watson
    import bb_odds
    off_data = points(cnx, 'offense')
    off_data = off_data.rename(columns = {i:'+'+i for i in list(off_data)})
    def_data = points(cnx, 'defense')
    def_data = def_data.rename(columns = {i:'-'+i for i in list(def_data)})
    del def_data['-pts']
    def_data *= -1
    cursor = cnx.cursor()
    query = 'SELECT * from gamedata;'
    cursor.execute(query)
    data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'opponent', 'location'])
    idx_switch = {}
    for t,d,o,l in np.array(data):
        idx_switch[str(d)+t.replace(' ', '_')] = str(d)+o.replace(' ', '_')
    idx = []
    for idxx in def_data.index:
        idx.append(idx_switch[idxx])
    def_data['idx'] = idx
    def_data = def_data.set_index('idx')
    data = def_data.join(off_data) 
    
    line = vegas_watson.rolling_vegas(pull_odds_data(cnx), bb_odds.teamnames, 'line')
    data = data.join(line, how = 'inner')
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data
    
def pace(cnx, od):
    if od == 'defense':
        cursor = cnx.cursor()
        query = 'SELECT `teamname`, `date`, `lasso_possessions`, `lightgbm_possessions`, `ridge_possessions` FROM defensive_preds as op;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'lasso_possessions', 'lightgbm_possessions', 'ridge_possessions'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        points = pull_possessions('pts_allowed', cnx)
        data = data.join(points, how = 'inner')
        return data 
    elif od == 'offense':
        cursor = cnx.cursor()
        query = 'SELECT teamname, date, lasso_possessions, lightgbm_possessions, linsvm_possessions FROM offensive_preds as dp;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'lasso_possessions', 'lightgbm_possessions', 'linsvm_possessions'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        points = pull_possessions('pts_scored', cnx)
        data = data.join(points, how = 'inner')
        return data 

  
def points(cnx, od):
    if od == 'defense':
        cursor = cnx.cursor()
        query = 'SELECT `teamname`, `date`, `lightgbm_all`, `ridge_all`, `lasso_team`, `lightgbm_team`, `linsvm_team`, `ridge_team`, `lasso_target`, `lightgbm_target` FROM defensive_preds as op;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'lightgbm_all', 'ridge_all', 'lasso_team', 'lightgbm_team', 'linsvm_team', 'ridge_team', 'lasso_target', 'lightgbm_target'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        rest = pull_days_rest(cnx)
        data = data.join(rest, how = 'inner')
        points = pull_pts('defensive', cnx)
        data = data.join(points, how = 'inner')
        return data
    elif od == 'offense':
        cursor = cnx.cursor()
        query = 'SELECT teamname, date, `linsvm_all`, `ridge_all`, lightgbm_team, linsvm_team, `lightgbm_target`, `ridge_target`, `lasso_target`, `linsvm_target` FROM offensive_preds as dp;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'linsvm_all', 'ridge_all', 'lightgbm_team', 'linsvm_team', 'lightgbm_target', 'ridge_target', 'lasso_target', 'linsvm_target'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        rest = pull_days_rest(cnx)
        data = data.join(rest, how = 'inner')
        points = pull_pts('offensive', cnx)
        data = data.join(points, how = 'inner')
        return data
    
    
def ppp(cnx, od):
    if od == 'offense':
        cursor = cnx.cursor()
        query = 'SELECT teamname, date, `linsvm_all`, `ridge_all`, lightgbm_team, linsvm_team,`lightgbm_target`, `ridge_target`, `lasso_target`, `linsvm_target` FROM offensive_preds as dp;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'linsvm_all', 'ridge_all', 'lightgbm_team', 'linsvm_team',  'lightgbm_target', 'ridge_target', 'lasso_target', 'linsvm_target'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        rest = pull_days_rest(cnx)
        data = data.join(rest, how = 'inner')
        points = pull_ppp('pts_scored', cnx)
        data = data.join(points, how = 'inner')
        return data  
    
    elif od == 'defense':
        cursor = cnx.cursor()
        query = 'SELECT `teamname`, `date`, `lightgbm_all`, `ridge_all`, `lasso_team`, `lightgbm_team`, `linsvm_team`, `ridge_team`, `lasso_target`, `lightgbm_target` FROM defensive_preds as op;'
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'lightgbm_all', 'ridge_all', 'lasso_team', 'lightgbm_team', 'linsvm_team', 'ridge_team', 'lasso_target', 'lightgbm_target'])
        idx = []
        for name, date in np.array(data[['teamname', 'date']]):
            idx.append(str(date)+name.replace(' ','_'))
        data['idx'] = idx
        data = data.set_index('idx')
        del data['teamname']
        del data['date']
        
        rest = pull_days_rest(cnx)
        data = data.join(rest, how = 'inner')
        points = pull_ppp('pts_allowed', cnx)
        data = data.join(points, how = 'inner')
        return data

    
def pull_ppp(od, cnx): 
    print('Loading Target Data')
    if od == 'pts_scored':
        selector = ['favscore', 'dogscore', 'favorite', 'underdog']
    elif od == 'pts_allowed':
        selector = ['dogscore', 'favscore', 'underdog', 'favorite']

    cursor = cnx.cursor()
    query = "select oddsdate, favorite,%s/`possessions-per-game` from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[0], selector[2])
    labels = ["oddsdate", "favorite","ppp"]
    cursor.execute(query)
    favdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(favdata):
        favid.append(str(date)+name.replace(' ','_'))
    favdata['idx'] = favid
    favdata = favdata.set_index('idx')
    favdata = favdata['ppp']
    query = "select oddsdate, underdog,%s/`possessions-per-game` from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[1], selector[3])
    labels = ["oddsdate", "underdog","ppp"]
    cursor.execute(query)
    dogdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(dogdata):
        favid.append(str(date)+name.replace(' ','_'))
    dogdata['idx'] = favid
    dogdata = dogdata.set_index('idx')
    dogdata = dogdata['ppp']
    data = favdata.append(dogdata)
    print('...Target Data Loaded')
    
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data
    
def pull_pts(od, cnx): 
    print('Loading Target Data')
    if od == 'offensive':
        selector = ['favscore', 'dogscore', 'favorite', 'underdog']
    elif od == 'defensive':
        selector = ['dogscore', 'favscore', 'underdog', 'favorite']

    cursor = cnx.cursor()
    query = "select oddsdate, favorite,%s from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[0], selector[2])
    labels = ["oddsdate", "favorite","pts"]
    cursor.execute(query)
    favdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(favdata):
        favid.append(str(date)+name.replace(' ','_'))
    favdata['idx'] = favid
    favdata = favdata.set_index('idx')
    favdata = favdata['pts']
    query = "select oddsdate, underdog,%s from oddsdata join basestats on oddsdata.oddsdate = basestats.statdate and oddsdata.%s = basestats.teamname" % (selector[1], selector[3])
    labels = ["oddsdate", "underdog","pts"]
    cursor.execute(query)
    dogdata = pd.DataFrame(cursor.fetchall(), columns = labels)
    favid = []
    for date, name, score in np.array(dogdata):
        favid.append(str(date)+name.replace(' ','_'))
    dogdata['idx'] = favid
    dogdata = dogdata.set_index('idx')
    dogdata = dogdata['pts']
    data = favdata.append(dogdata)
    print('...Target Data Loaded')
    
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.replace('NULL', np.nan)
    data = data.dropna(how = 'any')
    return data
    
def pull_model_features(y, x, mongodb_client):
#    y, x, mongodb_client = y_val, x_vals, update_dbs.mongodb_client
#    db['%s_%s'% (y.replace('_','-'), x.replace('_','-'))].find_one(sort=[('_game', -1)])   
    print('Loading Weighted Features')
    db = mongodb_client['ncaa_bb']
    weighted_stats = {}
    for each in db['%s_%s'% (y.replace('_','-'), x.replace('_','-'))].find():
        weighted_stats[each['_date']+each['_team']] = each['stats']
    weighted_stats = pd.DataFrame.from_dict(weighted_stats)
    weighted_stats = weighted_stats.T
    print('...Weighted Features Loaded')

    print('Loading Home/Away Features')
    db = mongodb_client['ncaa_bb']
    hfa_stats = {}
    for each in db['hfa-spread_%s_%s'% (y.replace('_','-'), x.replace('_','-'))].find():
        hfa_stats[each['_date']+each['_team']] = each['stats']
    hfa_stats = pd.DataFrame.from_dict(hfa_stats)
    hfa_stats = hfa_stats.T
    print('...Home/Away Features Loaded')
    
    if y == 'pts_scored':
        elo_tag = '_for'
    elif y == 'pts_allowed':
        elo_tag = '_allowed'
    print('Loading Elo Features')
    if x in ['defensive_stats', 'offensive_stats']:
        elo_stats = {}
        for each in db.elo_four_features.find():
            elo_stats[each['_date']+each['_team'].replace(' ', '_')] = each['stats'][x]
        elo_stats = pd.DataFrame.from_dict(elo_stats)
        elo_stats = elo_stats.T
        elo_stats = elo_stats.rename(columns = {i:i+elo_tag for i in list(elo_stats)})
    elif x in ['possessions', 'target']:
        elo_stats = {}
        for each in db.elo_four_features.find():
            elo_stats[each['_date']+each['_team'].replace(' ', '_')] = each['stats'][y][x]
        elo_stats = pd.DataFrame.from_dict(elo_stats)
        elo_stats = elo_stats.T
        elo_stats = elo_stats.rename(columns = {i:i+elo_tag for i in list(elo_stats)})
    print('...Elo Features Loaded')
    
    x_data = weighted_stats.join(elo_stats, how = 'inner')    
    x_data = x_data.join(hfa_stats, how = 'inner')
    x_data = x_data.replace([np.inf, -np.inf], np.nan)
    x_data = x_data.replace('NULL', np.nan)
    x_data = x_data.dropna(how = 'any')
    return x_data
