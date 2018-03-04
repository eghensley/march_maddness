import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
    try:
        import pandas as pd
    except ImportError:
        for loc in ['/usr/lib/python3.5','/usr/lib/python3.5/plat-x86_64-linux-gnu','/usr/lib/python3.5/lib-dynload','/usr/local/lib/python3.5/dist-packages','/usr/lib/python3/dist-packages']:
            sys.path.insert(-1, loc)
    try:
        import keras
    except ImportError:
        for loc in ['/usr/lib/python36.zip', '/usr/lib/python3.6', '/usr/lib/python3.6/lib-dynload', '/home/eric/ncaa_bb/lib/python3.6/site-packages']:
            sys.path.insert(-1, loc)
        sys.path.insert(-1, '/home/eric/stats_bb')
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
    try:
        import keras
    except ImportError:
        for loc in ['/usr/lib/python36.zip', '/usr/lib/python3.6', '/usr/lib/python3.6/lib-dynload', '/home/eric/ncaa_bb/lib/python3.6/site-packages']:
            sys.path.insert(-1, loc)
        sys.path.insert(-1, '/home/eric/stats_bb')

while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, os.path.join(cur_path, 'model_conf'))
sys.path.insert(-1, os.path.join(cur_path, 'db_utils'))
sys.path.insert(-1, os.path.join(cur_path, 'model_tuning'))
derived_folder = os.path.join(cur_path, 'derived_data')
model_storage = os.path.join(cur_path, 'saved_models')

import pull_data
import update_dbs
import saved_models
from sklearn.externals import joblib
import add_derived
import pandas as pd
import numpy as np
from keras.models import load_model

def update():
    train_index = pull_data.update_idx(update_dbs.mysql_client(), 'rankings')  
    update_df = pd.DataFrame()
    update_df['idx'] = train_index
    update_df = update_df.set_index('idx')
    for x_vals in ['offense', 'defense']:  
        for y_val in ['pace', 'ppp']:
            if y_val == 'ppp':
                data = pull_data.ppp(update_dbs.mysql_client(), x_vals)
                y_data = data[[y_val]]
                x_feats = list(data)
                x_feats.remove(y_val)
                x_data = data[x_feats]
                data = x_data.join(y_data, how = 'inner')
                data = data.loc[data.index.isin(train_index)]
                x_data = data[x_feats]                       
                y_data = data[[y_val]]
            elif y_val == 'pace':
                data = pull_data.pace(update_dbs.mysql_client(), x_vals)
                y_data = data[['possessions']]
                x_feats = list(data)
                x_feats.remove('possessions')
                x_data = data[x_feats]                       
                data = x_data.join(y_data, how = 'inner')
                data = data.loc[data.index.isin(train_index)]
                x_data = data[x_feats]                       
                y_data = data[['possessions']]
            
            if os.path.isfile(os.path.join(model_storage, '%s_%s_regression_model.pkl' % (y_val, x_vals))):
                print('Loading %s_%s'%(x_vals, y_val))
                model = joblib.load(os.path.join(model_storage, '%s_%s_regression_model.pkl' % (y_val, x_vals))) 
                scale = joblib.load(os.path.join(model_storage, '%s_%s_regression_scaler.pkl' % (y_val, x_vals))) 
                preds = model.predict(scale.fit_transform(x_data[saved_models.stored_models[x_vals][y_val]['features']]))
                indy_pred = pd.DataFrame()
                indy_pred[x_vals+'_'+y_val] = preds
                indy_pred['idx'] = list(x_data.index)
                indy_pred = indy_pred.set_index('idx')
                update_df = update_df.join(indy_pred, how = 'inner')
                print('Loaded %s_%s'%(x_vals, y_val))
                           
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
        train_index = pull_data.update_idx(update_dbs.mysql_client(), 'rankings') 
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
    x_data_stable = pull_data.share(update_dbs.mysql_client())
    data = data.join(x_data_stable, how = 'inner')
    save_index = list(data.index)
    
    data = data.reset_index()            
    x_vals = 'share'
    for y_val in ['+pts', 'keras']: 
        
        if os.path.isfile(os.path.join(model_storage, '%s_%s_regression_model.pkl' % (y_val, x_vals))) or os.path.isfile(os.path.join(model_storage, '%s_%s_regression_model.h5' % (y_val, x_vals))) :
            print('Loading %s_%s'%(x_vals, y_val))
            scale = joblib.load(os.path.join(model_storage,  '%s_%s_regression_scaler.pkl' % (y_val, x_vals))) 

            if y_val != 'keras':
                model = joblib.load(os.path.join(model_storage,  '%s_%s_regression_model.pkl' % (y_val, x_vals)))            
                preds = model.predict(scale.fit_transform(data[saved_models.stored_models[x_vals][y_val]['features']]))
                preds = list(preds)
            else:    
                model = load_model(os.path.join(model_storage, '%s_%s_regression_model.h5' % (y_val, x_vals))) 
                preds = model.predict(scale.fit_transform(data[saved_models.stored_models[x_vals][y_val]['features']]))
                preds = [i[0] for i in preds]

            indy_pred = pd.DataFrame()
            indy_pred['%s_%s' % (y_val, x_vals)] = preds                        

            indy_pred['idx'] = save_index
            indy_pred = indy_pred.set_index('idx')
            update_df = update_df.join(indy_pred, how = 'inner')
            print('Loaded %s'%(y_val))            
        
    update_df = update_df[['defense_pace', 'defense_ppp', 'offense_pace', 'offense_ppp', '+pts_share', 'keras_share']]
    add_derived.update('predictions', update_df)        