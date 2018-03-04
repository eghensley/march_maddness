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

import lasso_tuning
import ridge_tuning
import lgb_tuning
import linsvm_tuning
import pull_data
import update_dbs
import random
import numpy as np

train_index = pull_data.pull_train_index(update_dbs.mysql_client())
random.seed(86)
random.shuffle(train_index)
derived_data = {}
cnx = update_dbs.mysql_client()
x_vals = 'predictive'
y_val = '+pts'
x_data_stable = pull_data.score(update_dbs.mysql_client())
#x_data_stable = pull_data.share(update_dbs.mysql_client())
x_data_stable = x_data_stable.loc[x_data_stable.index.isin(train_index)]
x_cols = list(x_data_stable)
x_cols.remove(y_val)
x_cols.remove('+possessions')
x_cols.remove('-possessions')
y_data = x_data_stable['+pts'] 
x_data = x_data_stable[x_cols]   

y_data = np.ravel(y_data)
x_data = x_data_stable[x_cols]
result = lasso_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
print("Best %s %s score: %s" % (x_vals, y_val, result))
 
x_data = x_data_stable[x_cols]   
result = ridge_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
print("Best %s %s score: %s" % (x_vals, y_val, result))               

x_data = x_data_stable[x_cols]   
result = linsvm_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
print("Best %s %s score: %s" % (x_vals, y_val, result)) 
        
x_data = x_data_stable[x_cols]   
result = lgb_tuning.execute(y_val, x_vals, X_data = x_data, Y_data = y_data)
print("Best %s %s score: %s" % (x_vals, y_val, result))  
