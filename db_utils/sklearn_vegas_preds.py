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
model_storage = os.path.join(cur_path, 'saved_models')

import numpy as np
import pull_data
import update_dbs
import random
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
import saved_models
from sklearn.externals import joblib

validation_index = pull_data.pull_validation_index(update_dbs.mysql_client())
random.seed(86)

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
    x_data = x_data.loc[x_data.index.isin(validation_index)]
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

def sklearn_preds():
    raw_x = raw_data()
    x_score = pull_data.score(update_dbs.mysql_client())
    y_wl = pull_data.pull_wl(update_dbs.mysql_client())
    x_ou = pull_data.ou_preds(update_dbs.mysql_client())
    y_ou = pull_data.ou_wl(update_dbs.mysql_client())
    y_line = pull_data.line_wl(update_dbs.mysql_client())
    x_line = pull_data.line_preds(update_dbs.mysql_client())
    
    
    all_x_data = {'winner':{
                        '+pts': x_score.join(y_wl, how = 'inner'),
                        'raw': raw_x.join(y_wl, how = 'inner'),
                            },
                    'line':{
                        '+pts': x_score.join(y_line, how = 'inner').join(x_line, how = 'inner'),
                        'raw': raw_x.join(y_line, how = 'inner').join(x_line, how = 'inner'),                        
                            },
                    'ou':{
                        '+pts': x_score.join(y_ou, how = 'inner').join(x_ou, how = 'inner'),
                        'raw': raw_x.join(y_ou, how = 'inner').join(x_ou, how = 'inner'),                        
                            },
                        }
        
    all_y_data = {'winner':{
                        '+pts': x_score.join(y_wl, how = 'inner')['outcome'],
                        'raw': raw_x.join(y_wl, how = 'inner')['outcome'],
                            },
                    'line':{
                        '+pts': x_score.join(y_line, how = 'inner').join(x_line, how = 'inner')['line'],
                        'raw': raw_x.join(y_line, how = 'inner').join(x_line, how = 'inner')['line'],                        
                            },
                    'ou':{
                        '+pts': x_score.join(y_ou, how = 'inner').join(x_ou, how = 'inner')['ou'],
                        'raw': raw_x.join(y_ou, how = 'inner').join(x_ou, how = 'inner')['ou'],                        
                            },
                        }
    
    raw_x = None
    x_score = None
    y_wl = None
    x_ou = None
    y_ou = None
    y_line = None
    x_line = None
    random.seed(86)
    for sort in ['ou', 'winner', 'line']:
        outcomes = pd.DataFrame()
#        outcomes[sort] = np.ravel(all_y_data[sort]['raw'])
        outcomes['idx'] = list(all_y_data[sort]['raw'].index)
        outcomes = outcomes.set_index('idx')
        
        print('... starting %s' % (sort))
        for kind in ['raw', '+pts']: 
            print('... starting %s' % (kind))
            for model_name, model_details in saved_models.stored_models[sort][kind].items():
                if model_name == 'keras':
                    continue
                
                if os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (sort, kind, model_name))):
                    print('Evaluating %s '%(model_name))
    
                    model = joblib.load(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (sort, kind, model_name))) 
                    scale = joblib.load(os.path.join(model_storage, '%s_%s_%s_scaler.pkl' % (sort, kind, model_name))) 
    
                    preds = model.predict_proba(scale.transform(all_x_data[sort][kind][model_details['features']]))
                    model_outcome = pd.DataFrame()
                    winner = []
                    confidence = []
                    for game in preds:
                        if game[0] > game[1]:
                            winner.append(0)
                            confidence.append(game[0])
                        else:
                            winner.append(1)
                            confidence.append(game[1])
                    
#                    print('Accuracy: %s' % (accuracy_score(np.ravel(all_y_data[sort][kind]), winner)))
#                    print('Log Loss: %s' % (log_loss(np.ravel(all_y_data[sort][kind]), preds)))
                    
                    model_outcome['idx'] = list(all_x_data[sort][kind][model_details['features']].index)
                    model_outcome['%s_%s_prediction' % (kind, model_name)] = winner
                    model_outcome['%s_%s_confidence' % (kind, model_name)] = confidence
                    model_outcome = model_outcome.set_index('idx')
    
                    outcomes = outcomes.join(model_outcome, how = 'inner')
            print('Finished %s' % (kind))
        print('Finished %s' % (sort))                    
        outcomes.to_csv(os.path.join(output_folder, '%s_results.csv' % (sort)))