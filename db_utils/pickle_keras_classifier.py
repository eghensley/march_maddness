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

output_folder = os.path.join(cur_path, 'model_results')
features_folder = os.path.join(cur_path, 'feature_dumps')
model_storage = os.path.join(cur_path, 'saved_models')

import numpy as np
import pull_data
import update_dbs
import random
import saved_models
import pandas as pd
from sklearn.externals import joblib

def save():
    train_index = pull_data.pull_train_index(update_dbs.mysql_client())
    random.seed(86)
    random.shuffle(train_index)
    
    def hfa_patch(x, cnx):
        print('Running HFA Patch')
        keep_stats = []
        patch_stats = []
        for stat in list(x):
            try:
                stat.split('_HAspread_')[1]
                patch_stats.append(stat)
            except IndexError:
                keep_stats.append(stat)
        
        patch_data = x[patch_stats]
        keep_data = x[keep_stats]
        cursor = cnx.cursor()
        query = 'Select oddsdate, favorite, underdog, homeaway from oddsdata;'
        cursor.execute(query)
        patch = pd.DataFrame(cursor.fetchall(), columns = ['date', 't1', 't2', 'location'])
        cursor.close()
        
        loc_adj = {}
        for d,t1, t2,l in np.array(patch):
            if l == 0:
                loc_adj[str(d)+t1.replace(' ', '_')] = 1
                loc_adj[str(d)+t2.replace(' ', '_')] = -1     
            else:
                loc_adj[str(d)+t1.replace(' ', '_')] = -1
                loc_adj[str(d)+t2.replace(' ', '_')] = 1
        patch = None 
        
        patch_data = patch_data.join(pd.DataFrame.from_dict(list(loc_adj.items())).set_index(0), how = 'left')
        away_data = patch_data[patch_data[1]==-1]
        away_data *= -1
        home_data = patch_data[patch_data[1]==1]
        patch_data = home_data.append(away_data)
        del patch_data[1]
        x = patch_data.join(keep_data)
        print('Completed HFA Patch')
        return x
    
    def raw_data():
        def_data = pull_data.pull_model_features('pts_scored', 'defensive_stats', update_dbs.mongodb_client)
        def_data = hfa_patch(def_data, update_dbs.mysql_client())            
        off_data = pull_data.pull_model_features('pts_scored', 'offensive_stats', update_dbs.mongodb_client)
        off_feats = [i for i in list(off_data) if i not in list(def_data)]
        off_data = off_data[off_feats]
        off_data = hfa_patch(off_data, update_dbs.mysql_client())
        poss_data = pull_data.pull_model_features('pts_scored', 'possessions', update_dbs.mongodb_client)
        poss_data = hfa_patch(poss_data, update_dbs.mysql_client())  
        tar_data = pull_data.pull_model_features('pts_scored', 'target', update_dbs.mongodb_client)
        tar_data = hfa_patch(tar_data, update_dbs.mysql_client())  
        x_data = def_data.join(off_data, how = 'inner')   
        x_data = x_data.join(poss_data, how = 'inner')
        x_data = x_data.join(tar_data, how = 'inner')
        train_index = pull_data.pull_train_index(update_dbs.mysql_client())
        x_data = x_data.loc[x_data.index.isin(train_index)]
        y_data = pull_data.pull_pts('offensive', update_dbs.mysql_client())
        team_data = x_data.join(y_data, how = 'inner')[list(x_data)]
        def_data = None
        off_data = None
        poss_data = None
        tar_data = None
           
        def_data = pull_data.pull_model_features('pts_allowed', 'defensive_stats', update_dbs.mongodb_client)
        def_data = hfa_patch(def_data, update_dbs.mysql_client())            
        off_data = pull_data.pull_model_features('pts_allowed', 'offensive_stats', update_dbs.mongodb_client)
        off_feats = [i for i in list(off_data) if i not in list(def_data)]
        off_data = off_data[off_feats]
        off_data = hfa_patch(off_data, update_dbs.mysql_client())
        poss_data = pull_data.pull_model_features('pts_allowed', 'possessions', update_dbs.mongodb_client)
        poss_data = hfa_patch(poss_data, update_dbs.mysql_client())  
        tar_data = pull_data.pull_model_features('pts_allowed', 'target', update_dbs.mongodb_client)
        tar_data = hfa_patch(tar_data, update_dbs.mysql_client())  
        x_data = def_data.join(off_data, how = 'inner')   
        x_data = x_data.join(poss_data, how = 'inner')
        opponent_data = x_data.join(tar_data, how = 'inner')
        def_data = None
        off_data = None
        poss_data = None
        tar_data = None
         
        cnx = update_dbs.mysql_client()           
        cursor = cnx.cursor()
        query = 'SELECT * from gamedata;'
        cursor.execute(query)
        switch = pd.DataFrame(cursor.fetchall(), columns = ['teamname', 'date', 'opponent', 'location'])
        idx_switch = {}
        for t,d,o,l in np.array(switch):
            idx_switch[str(d)+t.replace(' ', '_')] = str(d)+o.replace(' ', '_')
        idx = []
        for idxx in opponent_data.index:
            idx.append(idx_switch[idxx])
        opponent_data['idx'] = idx
        opponent_data = opponent_data.set_index('idx')
        opponent_data *= -1
        opponent_data = opponent_data.rename(columns = {i:'-'+i for i in list(opponent_data)})
        data = opponent_data.join(team_data) 
        data = data.join(y_data, how = 'inner')
        data = data.replace([np.inf, -np.inf], np.nan)
        data = data.replace('NULL', np.nan)
        data = data.dropna(how = 'any')
        return data
    raw_x = raw_data()
    x_score = pull_data.score(update_dbs.mysql_client())
    raw_x = raw_x.join(x_score, how = 'inner')
    
    line = pull_data.pull_odds_data(update_dbs.mysql_client())
    idx = []
    gameline = []
    line_data = line[['fav_idx', 'dog_idx', 'line']]
    for fix, dix, ln in np.array(line_data):
        idx.append(fix)
        idx.append(dix)
        gameline.append(ln)
        gameline.append(ln * -1)
        
    linedata = pd.DataFrame()
    linedata['idx'] = idx
    linedata['vegas_line'] = gameline
    linedata = linedata.set_index('idx')
    
    idx = []
    gameou = []
    ou_data = line[['fav_idx', 'dog_idx', 'overunder']]
    for fix, dix, ou in np.array(ou_data):
        idx.append(fix)
        idx.append(dix)
        gameou.append(ou)
        gameou.append(ou * -1)
        
    oudata = pd.DataFrame()
    oudata['idx'] = idx
    oudata['vegas_ou'] = gameou
    oudata = oudata.set_index('idx')
    
    raw_x = raw_x.join(oudata, how = 'inner')
    raw_x = raw_x.join(linedata, how = 'inner')
    
    y_wl = pull_data.pull_wl(update_dbs.mysql_client())
    x_ou = pull_data.ou_preds(update_dbs.mysql_client())
    y_ou = pull_data.ou_wl(update_dbs.mysql_client())
    y_line = pull_data.line_wl(update_dbs.mysql_client())
    x_line = pull_data.line_preds(update_dbs.mysql_client())
    
    
    all_x_data = {'winner':{'raw': raw_x.join(y_wl, how = 'inner')},
                'line':{'raw': raw_x.join(y_line, how = 'inner').join(x_line, how = 'inner')},
                'ou':{'raw': raw_x.join(y_ou, how = 'inner').join(x_ou, how = 'inner')},
                }
        
    all_y_data = {'winner':{'raw': raw_x.join(y_wl, how = 'inner')['outcome']},
                'line':{'raw': raw_x.join(y_line, how = 'inner').join(x_line, how = 'inner')['line']},
                'ou':{'raw': raw_x.join(y_ou, how = 'inner').join(x_ou, how = 'inner')['ou']},
                }
    
    raw_x = None
    x_score = None
    y_wl = None
    x_ou = None
    y_ou = None
    y_line = None
    x_line = None
    random.seed(86)
    for kind in ['keras']:
        print('... starting %s' % (kind))
        for sort in ['winner', 'line', 'ou']: 
            print('... starting %s' % (sort))
            if not os.path.isfile(os.path.join(model_storage, '%s_%s_regression.h5' % (sort,kind))):
        
                X = all_x_data[sort]['raw']
                X = X.reset_index()
                X = X[saved_models.stored_models[sort]['raw'][kind]['features']]
                Y = all_y_data[sort]['raw']
                Y = Y.reset_index()
                if sort != 'winner':
                    Y = Y[sort]
                else:
                    Y = Y['outcome']
                
                print('...storing %s Keras'%(sort))
                
                
                model = saved_models.stored_models[sort]['raw'][kind]['model']
                scale = saved_models.stored_models[sort]['raw'][kind]['scale']
            
                scale.fit(X[saved_models.stored_models[sort]['raw'][kind]['features']])
                joblib.dump(scale,os.path.join(model_storage, '%s_%s_regression_scaler.pkl' % (sort,kind)))             
                model.fit(scale.transform(X[saved_models.stored_models[sort]['raw'][kind]['features']]), np.ravel(Y))
                model.model.save(os.path.join(model_storage, '%s_%s_regression_model.h5' % (sort,kind))) 
            
                print('Stored %s_%s'%(sort,kind))
                
            print('Finished %s' % (sort))
        print('Finished %s' % (kind))
    
