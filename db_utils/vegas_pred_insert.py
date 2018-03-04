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
import saved_models
from sklearn.externals import joblib
import vegas_watson
import pandas as pd
import add_derived

def update():
    for x_vals in ['line', 'ou']:
        train_index = pull_data.update_idx(update_dbs.mysql_client(), '%s_preds' % (x_vals))  
        if len(train_index) == 0:
            continue
        update_df = pd.DataFrame()
        update_df['idx'] = train_index
        update_df = update_df.set_index('idx')
        
        y_val = 'result'
        print('Loading rolling betting stats')
        x_data_stable = vegas_watson.rolling_vegas(x_vals)
        print('... Loaded rolling betting stats')
        x_data_stable = x_data_stable.loc[x_data_stable.index.isin(train_index)]
        x_cols = list(x_data_stable)
        x_cols.remove(y_val)
        x_data_stable = x_data_stable[x_cols]
        for model_name, model_details in saved_models.stored_models[y_val][x_vals].items():
            if os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))):
                print('Loading %s Values'%(model_name))
                
                model = joblib.load(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))) 
                scale = joblib.load(os.path.join(model_storage, '%s_%s_%s_scaler.pkl' % (y_val, x_vals, model_name))) 
                
                preds = model.predict(scale.fit_transform(x_data_stable[model_details['features']]))
                indy_pred = pd.DataFrame()
                indy_pred[model_name+'_'+x_vals] = preds
                indy_pred['idx'] = list(x_data_stable.index)
                indy_pred = indy_pred.set_index('idx')
                update_df = update_df.join(indy_pred, how = 'inner')
                print('Loaded %s'%(model_name))
                
        for model_name in ['PCA', "TSVD"]:
            if os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))):
                print('Loading %s Values'%(model_name))
                model = joblib.load(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))) 
                if x_vals == 'ou':
                    feats = ['10_game_avg', '15_game_avg', '50_game_avg', '30_game_avg', 'streak', '5_game_avg', '3_game_avg']
                elif x_vals == 'line':
                    feats = ['10_game_avg', 'ha', 'streak', '50_game_avg']
                preds = model.fit_transform(x_data_stable[feats])
                indy_pred = pd.DataFrame()
                indy_pred['idx'] = list(x_data_stable.index)
                indy_pred[model_name+'_'+x_vals] = preds
                indy_pred = indy_pred.set_index('idx')
                update_df = update_df.join(indy_pred, how = 'inner')
                print('Loaded %s'%(model_name))            
            
        if x_vals == 'line':
            update_df = update_df[['PCA_line', 'TSVD_line', 'lasso_line', 'lightgbm_line', 'ridge_line']]      
            add_derived.update('%s_preds' % (x_vals), update_df)
            
        elif x_vals == 'ou':
            update_df = update_df[['PCA_ou', 'TSVD_ou', 'lasso_ou', 'lightgbm_ou', 'ridge_ou']]      
            add_derived.update('%s_preds' % (x_vals), update_df)        


            
