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
output_folder = os.path.join(cur_path, 'model_results')
sys.path.insert(-1, output_folder)
f = open('keras_pts_scored.txt', 'a')
f.write('Starting Keras Analysis... \n')
f.close()

features_folder = os.path.join(cur_path, 'feature_dumps')
input_folder = os.path.join(cur_path, 'derived_data')
from keras import backend as K
import pull_data
import update_dbs
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
import feature_lists
from sklearn.model_selection import ShuffleSplit, StratifiedKFold
import matplotlib.pyplot as plt
import pandas as pd

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

def retrieve_data():
            y_val = 'pts_scored'
            y_data = pull_data.pull_pts('offensive', update_dbs.mysql_client())
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
            train_index = pull_data.pull_train_index(update_dbs.mysql_client())
            x_data = x_data.loc[x_data.index.isin(train_index)]
            x_data = x_data.join(y_data, how = 'inner')[list(x_data)]
            def_data = None
            off_data = None
            poss_data = None
            tar_data = None
            data = x_data.join(y_data, how = 'inner')
            data = data.reset_index()
            Y = data['pts']
            x_feats = ['expected_pts_pg_for',
            '75_g_HAspread_for_floor-percentage',
            'pregame_pts_pg_for',
            'expected_poss_pg_for',
            'expected_ppp_for',
            '50_game_avg_15_g_HAweight_allow_assist--per--turnover-ratio',
            '75_g_HAspread_allow_points-per-game',
            '100_g_HAspread_allow_block-pct',
            'pregame_poss_pg_for',
            '10_game_avg_30_g_HAweight_allow_personal-foul-pct',
            'expected_turnovers-per-possession_for',
            'expected_offensive-rebounding-pct_for',
            '30_g_HAspread_for_floor-percentage',
            'expected_ftm-per-100-possessions_for',
            'expected_effective-field-goal-pct_for',
            'pregame_effective-field-goal-pct_for',
            '100_g_HAspread_allow_assist--per--turnover-ratio',
            '30_g_HAspread_allow_floor-percentage',
            '10_game_avg_30_g_HAweight_allow_two-point-rate',
            '5_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game',
            '10_game_avg_50_g_Tweight_for_effective-field-goal-pct',
            '30_game_avg_5_g_Tweight_for_points-per-game`/`possessions-per-game']
            X = data[x_feats]
            return X, Y

scaler = StandardScaler()
x_data, y_data = retrieve_data()    
def explained_variance(y_true, y_pred):
    ss_res = K.sum(K.square(y_true-y_pred))
    ss_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - ss_res/(ss_tot + K.epsilon()))

for width in np.linspace(1, 4, 8):
    for depth in range(1,4):
        def nn_model():
        	# create model
            model = Sequential()
            model.add(Dense(int(22*width), input_dim=22, kernel_initializer='normal', activation='relu'))
            for lay in range(depth):
                model.add(Dropout(.1))
                model.add(Dense(int((float(22*width)/(depth+1))*(depth-lay)), kernel_initializer='normal', activation='relu'))
            model.add(Dense(1, kernel_initializer='normal'))
        	# Compile model
            model.compile(loss='mean_squared_error', optimizer='SGD', metrics=[explained_variance])
            return model 
        
        model = nn_model()
        for test_idx, train_idx in ShuffleSplit(n_splits=1, test_size=0.90, random_state=86).split(x_data, y_data):
            history = model.fit(scaler.fit_transform(x_data.loc[train_idx]), np.ravel(y_data.loc[train_idx]), epochs=75, batch_size=64, verbose=1, validation_data=(scaler.fit_transform(x_data.loc[test_idx]), np.ravel(y_data.loc[test_idx])), shuffle = True)
            plt.plot(history.history['loss'][3:], linestyle = '-.')
            plt.plot(history.history['val_loss'][3:], linestyle = ':')            
            plt.title('model loss')
            plt.ylabel('loss')
            plt.xlabel('epoch')
            plt.legend(['train', 'test'], loc='upper left')
            plt.show()
            
            plt.plot(history.history['explained_variance'][3:], linestyle = '-.')
            plt.plot(history.history['val_explained_variance'][3:], linestyle = ':')            
            plt.title('model loss')
            plt.ylabel('loss')
            plt.xlabel('epoch')
            plt.legend(['train', 'test'], loc='upper left')
            plt.show()
            f = open('keras_pts_scored.txt', 'a')
            f.write('width: %s: depth: %s. best mse: %s,  r2: %s' % (width, depth, min(history.history['val_explained_variance']), list(history.history['val_loss'])[list(history.history['val_loss']).index(min(history.history['val_loss']))]))
            f.close()


#for width in [2.5]:
#    for depth in ['elu']:
#        def nn_model():
#            model = Sequential()
#            model.add(Dense(int(22*width), input_dim=22, kernel_initializer='normal', activation=depth))
#            model.add(Dropout(.1))
#            model.add(Dense(int((float(22*width)/(2))), kernel_initializer='normal', activation=depth))
#            model.add(Dropout(.1))
#            model.add(Dense(1, kernel_initializer='normal'))
#            model.compile(loss='mean_squared_error', optimizer='adam')
#            return model
#
#        model = nn_model()
#        for test_idx, train_idx in ShuffleSplit(n_splits=1, test_size=0.90, random_state=86).split(X, Y):
#            history = model.fit(scaler.fit_transform(X.loc[train_idx]), np.ravel(Y.loc[train_idx]), epochs=5000, batch_size=16, verbose=1, validation_data=(scaler.fit_transform(X.loc[test_idx]), np.ravel(Y.loc[test_idx])), shuffle = True)
#            plt.plot(history.history['loss'], linestyle = '-.')
#            plt.plot(history.history['val_loss'], linestyle = ':')            
#            plt.title('model loss')
#            plt.ylabel('loss')
#            plt.xlabel('epoch')
#            plt.legend(['train', 'test'], loc='upper left')
#            plt.show()
#        f = open('keras_pts_scored.txt', 'a')
#        f.write('%s %s: %s @ %s \n' % (width, depth, min(history.history['val_loss']), list(history.history['val_loss']).index(min(history.history['val_loss']))))
#        f.close()


        
#def baseline_model():
#	# create model
#	model = Sequential()
#	model.add(Dense(22, input_dim=22, kernel_initializer='normal', activation='relu'))
#	model.add(Dense(1, kernel_initializer='normal'))
#	# Compile model
#	model.compile(loss='mean_squared_error', optimizer='adam')
#	return model

#def test_scaler(x, y):
#    print('Searching for best scaler...')
#    scores = []
#    model = baseline_model()
#    for scale in [StandardScaler(), MinMaxScaler(), RobustScaler()]:
#        for test_idx, train_idx in ShuffleSplit(n_splits=1, test_size=0.90, random_state=86).split(x, y):
#            history = model.fit(scale.fit_transform(x.loc[train_idx]), np.ravel(y.loc[train_idx]), epochs=200, batch_size=64, verbose=1, validation_data=(scale.fit_transform(x.loc[test_idx]), np.ravel(y.loc[test_idx])), shuffle = True)
#            scores.append(min(history.history['val_loss']))
#            plt.plot(history.history['loss'], linestyle = '-.')
#            plt.plot(history.history['val_loss'], linestyle = ':')            
#            plt.title('model loss')
#            plt.ylabel('loss')
#            plt.xlabel('epoch')
#            plt.legend(['train', 'test'], loc='upper left')
#            plt.show()
#        f = open('keras_pts_scored.txt', 'a')
#        f.write('%s: %s.  ' % (scale, min(history.history['val_loss'])))
#        f.close()
#    if scores.index(min(scores)) == 0:
#        print('Using Standard Scaler')
#        return StandardScaler()
#    elif scores.index(min(scores)) == 1:
#        print('Using Min Max Scaler')
#        return MinMaxScaler()
#    elif scores.index(min(scores)) == 2:
#        print('Using Robust Scaler')
#        return RobustScaler()
#
#X, Y = retrieve_data()    
#scaler = test_scaler(X, Y) #RobustScaler
#f = open('keras_pts_scored.txt', 'a')
#f.write('Scaler: %s  \n' % (scaler))
#f.close()