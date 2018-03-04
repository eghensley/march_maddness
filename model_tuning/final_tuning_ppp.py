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
input_folder = os.path.join(cur_path, 'derived_data')

import pandas as pd
import lasso_tuning
import ridge_tuning
import lgb_tuning
import linsvm_tuning
import numpy as np

for x_vals in ['for', 'allowed']:
    for y_val in ['ppp']:
        x_data_stable = pd.read_csv(os.path.join(input_folder, '%s_%s_derived.csv' % (x_vals, y_val)))
        x_data_stable = x_data_stable.set_index('Unnamed: 0')
        y_data = np.ravel(x_data_stable[['ppp_ppp']]) 
        x_cols = list(x_data_stable)
        x_cols.remove('ppp_ppp')

            
        y_val = y_val+'_derived'
        x_data_stable = x_data_stable[x_cols]
        x_data = x_data_stable   
        result = lgb_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
        print("Best %s %s score: %s" % (x_vals, y_val, result))  
        
        
        x_data = x_data_stable   
        result = lasso_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
        print("Best %s %s score: %s" % (x_vals, y_val, result))
 
        x_data = x_data_stable   
        result = ridge_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
        print("Best %s %s score: %s" % (x_vals, y_val, result))               

        x_data = x_data_stable   
        result = linsvm_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
        print("Best %s %s score: %s" % (x_vals, y_val, result)) 