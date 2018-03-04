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
model_storage = os.path.join(cur_path, 'saved_models')

import pull_data
import update_dbs
import pandas as pd
import numpy as np
import saved_models
from sklearn.externals import joblib
import add_derived

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

    cursor = cnx.cursor()
    query = 'Select oddsdate, favorite, underdog, homeaway from future_games;'
    cursor.execute(query)
    patch_fut = pd.DataFrame(cursor.fetchall(), columns = ['date', 't1', 't2', 'location'])
    cursor.close()
    
    patch = patch.append(patch_fut)
    
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
    print('...Completed HFA Patch')
    return x

def update():
    for y_val in ['pts_scored', 'pts_allowed']: 
        if y_val == 'pts_scored':
            train_index = pull_data.update_idx(update_dbs.mysql_client(), 'offensive_preds')
        if y_val == 'pts_allowed':
            train_index = pull_data.update_idx(update_dbs.mysql_client(), 'defensive_preds')   
        update_df = pd.DataFrame()
        if len(train_index) == 0:
            continue
        update_df['idx'] = train_index
        update_df = update_df.set_index('idx')
        for x_vals in ['defensive_stats', 'offensive_stats', 'full-team', 'all', 'possessions', 'target']:
            if x_vals in ['defensive_stats', 'offensive_stats'] and y_val == 'pts_allowed':
                continue
            if x_vals in ['full-team', 'defensive_stats'] and y_val == 'pts_scored':
                continue      
    
            if x_vals == 'possessions':
                y_data = pull_data.pull_possessions(y_val, update_dbs.mysql_client())
                x_data = pull_data.pull_model_features(y_val, x_vals, update_dbs.mongodb_client)
                x_data = hfa_patch(x_data, update_dbs.mysql_client())             
                x_data = x_data.loc[x_data.index.isin(train_index)]
                y_data = x_data.join(y_data, how = 'inner')['possessions']
                x_data = x_data.join(y_data, how = 'inner')[list(x_data)]
                
            elif x_vals in ['target', 'defensive_stats', 'offensive_stats', 'full-team', 'all']:
                y_data = pull_data.pull_ppp(y_val, update_dbs.mysql_client())
                
                
            if x_vals == 'full-team':
                def_data = pull_data.pull_model_features(y_val, 'defensive_stats', update_dbs.mongodb_client)
                def_data = hfa_patch(def_data, update_dbs.mysql_client())            
                off_data = pull_data.pull_model_features(y_val, 'offensive_stats', update_dbs.mongodb_client)
                off_feats = [i for i in list(off_data) if i not in list(def_data)]
                off_data = off_data[off_feats]
                off_data = hfa_patch(off_data, update_dbs.mysql_client())
                x_data = def_data.join(off_data, how = 'inner')       
                x_data = x_data.loc[x_data.index.isin(train_index)]
                y_data = x_data.join(y_data, how = 'inner')['ppp']
                x_data = x_data.join(y_data, how = 'inner')[list(x_data)]
                off_data = None
                def_data = None
    
            elif x_vals == 'all':
                def_data = pull_data.pull_model_features(y_val, 'defensive_stats', update_dbs.mongodb_client)
                def_data = hfa_patch(def_data, update_dbs.mysql_client())            
                off_data = pull_data.pull_model_features(y_val, 'offensive_stats', update_dbs.mongodb_client)
                off_feats = [i for i in list(off_data) if i not in list(def_data)]
                off_data = off_data[off_feats]
                off_data = hfa_patch(off_data, update_dbs.mysql_client())
                poss_data = pull_data.pull_model_features(y_val, 'possessions', update_dbs.mongodb_client)
                poss_data = hfa_patch(poss_data, update_dbs.mysql_client())  
                tar_data = pull_data.pull_model_features(y_val, 'target', update_dbs.mongodb_client)
                tar_data = hfa_patch(tar_data, update_dbs.mysql_client())  
                x_data = def_data.join(off_data, how = 'inner')   
                x_data = x_data.join(poss_data, how = 'inner')
                x_data = x_data.join(tar_data, how = 'inner')
                x_data = x_data.loc[x_data.index.isin(train_index)]
                y_data = x_data.join(y_data, how = 'inner')['ppp']
                x_data = x_data.join(y_data, how = 'inner')[list(x_data)]
                def_data = None
                off_data = None
                poss_data = None
                tar_data = None
               
            elif x_vals in ['target', 'defensive_stats', 'offensive_stats']:
                x_data = pull_data.pull_model_features(y_val, x_vals, update_dbs.mongodb_client)
                x_data = hfa_patch(x_data, update_dbs.mysql_client())             
                x_data = x_data.loc[x_data.index.isin(train_index)]
                y_data = x_data.join(y_data, how = 'inner')['ppp']
                x_data = x_data.join(y_data, how = 'inner')[list(x_data)]     
            
            for model_name, model_details in saved_models.stored_models[y_val][x_vals].items():
                if os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))):
                    print('Loading %s Values'%(model_name))
                    
                    model = joblib.load(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))) 
                    scale = joblib.load(os.path.join(model_storage, '%s_%s_%s_scaler.pkl' % (y_val, x_vals, model_name))) 
                    
                    preds = model.predict(scale.fit_transform(x_data[model_details['features']]))
                    indy_pred = pd.DataFrame()
                    if x_vals == 'offensive_stats':
                        indy_pred[model_name+'_team'] = preds
                    elif y_val == 'pts_allowed' and x_vals == 'full-team':
                        indy_pred[model_name+'_team'] = preds                        
                    else:
                        indy_pred[model_name+'_'+x_vals] = preds
                    indy_pred['idx'] = list(x_data.index)
                    indy_pred = indy_pred.set_index('idx')
                    update_df = update_df.join(indy_pred, how = 'inner')
                    print('Loaded %s'%(model_name))
                    
        if y_val == 'pts_scored':
            update_df = update_df[['lightgbm_team', 'linsvm_team', 'linsvm_all', 'ridge_all', 'lasso_possessions', 'lightgbm_possessions', 'linsvm_possessions', 'lightgbm_target', 'linsvm_target', 'ridge_target', 'lasso_target']]
            add_derived.update('offensive_preds', update_df)
    
        elif y_val == 'pts_allowed':
            update_df = update_df[['lightgbm_all', 'ridge_all', 'lasso_team', 'lightgbm_team', 'linsvm_team', 'ridge_team', 'lasso_possessions', 'lightgbm_possessions', 'ridge_possessions', 'lasso_target', 'lightgbm_target']]
            add_derived.update('defensive_preds', update_df)