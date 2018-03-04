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
sys.path.insert(-1, output_folder)
f = open('keras_model_tuning.txt', 'w')
f.write('Starting Keras Analysis...')
f.close()

features_folder = os.path.join(cur_path, 'feature_dumps')
input_folder = os.path.join(cur_path, 'derived_data')
import pull_data
import update_dbs
import numpy as np
import pandas as pd
import polysvc_tuning
import rbfsvc_tuning

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
data = raw_data()
x_cols = ['expected_effective-field-goal-pct_for',
'10_game_avg_30_g_Tweight_for_true-shooting-percentage',
'-75_g_HAspread_allow_defensive-efficiency',
'100_g_HAspread_allow_block-pct',
'10_game_avg_10_g_Tweight_for_possessions-per-game',
'-expected_effective-field-goal-pct_allowed',
'75_g_HAspread_for_floor-percentage',
'-10_game_avg_15_g_HAweight_for_defensive-efficiency',
'-30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game',
'30_game_avg_5_g_Tweight_for_possessions-per-game',
'25_g_HAspread_for_points-per-game',
'-30_game_avg_50_g_HAweight_allow_points-per-game',
'-10_game_avg_10_g_Tweight_allow_points-per-game`/`possessions-per-game',
'-1_game_avg_10_g_Tweight_allow_possessions-per-game',
'-100_g_HAspread_for_points-per-game',
'-50_game_avg_50_g_HAweight_for_assists-per-game',
'25_g_HAspread_for_possessions-per-game',
'10_game_avg_50_g_HAweight_for_blocks-per-game',
'-50_game_avg_50_g_HAweight_allow_ftm-per-100-possessions',
'20_game_avg_30_g_HAweight_for_defensive-rebounds-per-game',
'-20_game_avg_50_g_Tweight_for_floor-percentage',
'20_game_avg_10_g_HAweight_for_possessions-per-game',
'-20_game_avg_50_g_Tweight_allow_points-per-game',
'-100_g_HAspread_allow_assist--per--turnover-ratio',
'-10_game_avg_10_g_HAweight_allow_points-per-game',
'75_g_HAspread_allow_percent-of-points-from-3-pointers',
'-15_g_HAspread_allow_block-pct',
'-20_game_avg_25_g_Tweight_allow_possessions-per-game',
'-10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game',
'-20_game_avg_50_g_HAweight_allow_defensive-efficiency',
'50_game_avg_50_g_HAweight_for_assists-per-game',
'-30_game_avg_25_g_Tweight_allow_points-per-game',
'-25_g_HAspread_allow_possessions-per-game']
y_data = pull_data.ou_wl(update_dbs.mysql_client())
ou_preds = pull_data.ou_preds(update_dbs.mysql_client())
all_data = data.join(y_data, how = 'inner')
all_data = all_data.join(ou_preds, how = 'inner')
y_data = np.ravel(all_data[['ou']])
for pred in list(ou_preds):
    x_cols.append(pred)
x_data_stable = all_data[x_cols]
    
#import linsvc_tuning
#import lgclass_tuning
#import log_tuning
#import knn_tuning
x_vals = 'raw'
y_val = 'ou'

#
#x_data = x_data_stable   
#result = polysvc_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
#print("Best %s %s score: %s" % (x_vals, y_val, result))  

x_data = x_data_stable   
result = rbfsvc_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
print("Best %s %s score: %s" % (x_vals, y_val, result))  


#x_data = x_data_stable   
#result = lgclass_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
#print("Best %s %s score: %s" % (x_vals, y_val, result)) 
#
#x_data = x_data_stable   
#result = linsvc_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
#print("Best %s %s score: %s" % (x_vals, y_val, result)) 

#x_data = x_data_stable   
#result = knn_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
#print("Best %s %s score: %s" % (x_vals, y_val, result))
# 
#x_data = x_data_stable   
#result = log_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
#print("Best %s %s score: %s" % (x_vals, y_val, result))  