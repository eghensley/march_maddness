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
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD
import pickle

train_index = pull_data.pull_train_index(update_dbs.mysql_client())

def save():
    for x_vals in ['line', 'ou']:
        y_val = 'result'
        print('Loading rolling betting stats')
        x_data_stable = vegas_watson.rolling_vegas(x_vals)
        print('... Loaded rolling betting stats')
        x_data_stable = x_data_stable.loc[x_data_stable.index.isin(train_index)]
        y_data = x_data_stable[[y_val]]
        x_cols = list(x_data_stable)
        x_cols.remove(y_val)
        x_data_stable = x_data_stable[x_cols]
        for model_name, model_details in saved_models.stored_models[y_val][x_vals].items():
            if not os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))):
                print('Loading %s Values'%(model_name))        
                
                model = model_details['model']
                scale = model_details['scale']
                
                scale.fit(x_data_stable[model_details['features']])
                joblib.dump(scale,os.path.join(model_storage, '%s_%s_%s_scaler.pkl' % (y_val, x_vals, model_name)))             
    
                model.fit(scale.transform(x_data_stable[model_details['features']]), np.ravel(y_data))
                if model_name != 'lightgbm':
                    joblib.dump(model,os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))) 
                else:
                    pickle_dump = open(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name)), 'wb')
                    pickle.dump(model, pickle_dump)
                    pickle_dump.close()
                print('Stored %s'%(model_name))
                
        for model_name, model in [('PCA', PCA(n_components = 1, random_state = 1108)), ("TSVD", TruncatedSVD(n_components = 1, random_state = 1108))]:
            if not os.path.isfile(os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))):
                print('Loading %s Values'%(model_name))
                if x_vals == 'ou':
                    feats = ['10_game_avg', '15_game_avg', '50_game_avg', '30_game_avg', 'streak', '5_game_avg', '3_game_avg']
                elif x_vals == 'line':
                    feats = ['10_game_avg', 'ha', 'streak', '50_game_avg']
                model.fit(x_data_stable[feats])
                joblib.dump(model,os.path.join(model_storage, '%s_%s_%s_model.pkl' % (y_val, x_vals, model_name))) 
                print('Stored %s'%(model_name))

