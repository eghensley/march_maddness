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
try:
    import lightgbm as lgb
except ImportError:
    sys.path.insert(-1, "/home/eric/LightGBM/python-package")
    import lightgbm as lgb
    
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.linear_model import Lasso, Ridge, LogisticRegression
from sklearn.svm import LinearSVR, SVC
from sklearn.neighbors import KNeighborsClassifier
from keras.models import Sequential
from keras.wrappers.scikit_learn import KerasClassifier, KerasRegressor
from keras.layers import Dense, Dropout
import keras.backend as K
import keras

def ou_nn():
    model = Sequential()
    model.add(Dense(76, input_dim=39, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.45))
    model.add(Dense(50, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.45))
    model.add(Dense(25, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.15))
    model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adagrad', metrics=['accuracy'])
    return model 

def line_nn():
    model = Sequential()
    model.add(Dense(87, input_dim=36, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(.4))
    model.add(Dense(44, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(.1))
    model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer=keras.optimizers.SGD(lr=.05, momentum=0.0, decay=0.0, nesterov=False), metrics=['accuracy'])
    return model 

def winner_nn():
    model = Sequential()
    model.add(Dense(48, input_dim=23, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.15))
    model.add(Dense(32, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.15))
    model.add(Dense(16, kernel_initializer='normal', activation='elu'))
    model.add(Dropout(.05))
    model.add(Dense(1, kernel_initializer='normal', activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer=keras.optimizers.SGD(lr=0.0005, momentum=0, decay=0.0), metrics=['accuracy'])
    return model

def explained_variance(y_true, y_pred):
    ss_res = K.sum(K.square(y_true-y_pred))
    ss_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - ss_res/(ss_tot + K.epsilon()))

def share_nn():
    model = Sequential()
    model.add(Dense(68, input_dim=25, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(.05))
    model.add(Dense(34, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(.05))
    model.add(Dense(1, kernel_initializer='normal'))
    model.compile(loss='mean_squared_error', optimizer=keras.optimizers.SGD(lr=.075, momentum=0.0, decay=0.0))#, metrics=[explained_variance])
    return model 

stored_models = {
        'offense':{
            'pace': {
                'features': ['lightgbm_possessions', 'lasso_possessions', 'linsvm_possessions'],
                'model': Lasso(random_state = 1108, alpha = 0.019012104600893226),
                'scale': StandardScaler(),
            },    
            'ppp': {
                'features': ['linsvm_team', 'ridge_all', 'rest', 'ridge_target', 'lightgbm_target', 'lightgbm_team', 'lasso_target', 'linsvm_all', 'linsvm_target'],
                'model': LinearSVR(random_state = 1108, C = 0.215329117725, epsilon=0),
                'scale': RobustScaler(),
            },                 
        },
        'defense':{
            'pace': {
                'features': ['lightgbm_possessions', 'lasso_possessions', 'ridge_possessions'],
                'model': LinearSVR(random_state = 1108, C = 0.6652011887133216, epsilon=0),
                'scale': MinMaxScaler(),
            },  
            'ppp': {
                'features': ['ridge_all', 'linsvm_team', 'ridge_team', 'rest', 'lightgbm_team', 'lightgbm_all', 'lasso_team', 'lasso_target', 'lightgbm_target'],
                'model': Ridge(random_state = 1108, solver = 'lsqr', alpha = 0.00101115979472),
                'scale': StandardScaler(),
            },  
        },
        'share':{
            '+pts': {
                'features': ['+ridge_all', 'pregame_ppp_for', '-75_g_HAspread_allow_floor-percentage', '-30_g_HAspread_for_offensive-efficiency', '-25_g_HAspread_allow_points-per-game`/`possessions-per-game', '-50_g_HAspread_allow_points-per-game`/`possessions-per-game', '100_g_HAspread_for_personal-fouls-per-game', '75_g_HAspread_for_shooting-pct', '-100_g_HAspread_for_points-per-game', '-lightgbm_team', '10_g_HAspread_allow_personal-fouls-per-possession', '-expected_pts_pg_allowed', '50_g_HAspread_for_points-per-game', '50_g_HAspread_allow_floor-percentage', '25_g_HAspread_for_points-per-game', '-linsvm_team', 'expected_offensive-rebounding-pct_for', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_turnovers-per-possession_for', '30_g_HAspread_for_steal-pct', '-pregame_turnovers-per-possession_allowed', 'pregame_turnovers-per-possession_for', '10_game_avg_50_g_HAweight_for_offensive-efficiency'],
                'model': Lasso(random_state = 1108, alpha = 0.001),
                'scale': StandardScaler(),                            
                },
            'keras':{
                'features': ['+ridge_all','expected_effective-field-goal-pct_for','expected_turnovers-per-possession_for','expected_offensive-rebounding-pct_for','-linsvm_team','25_g_HAspread_for_points-per-game','-pregame_turnovers-per-possession_allowed','50_g_HAspread_allow_floor-percentage','50_g_HAspread_for_points-per-game','-expected_pts_pg_allowed','10_game_avg_50_g_HAweight_for_offensive-efficiency','30_g_HAspread_for_steal-pct','10_g_HAspread_allow_personal-fouls-per-possession','pregame_turnovers-per-possession_for','-10_game_avg_15_g_HAweight_for_assist--per--turnover-ratio','-100_g_HAspread_for_points-per-game','75_g_HAspread_for_shooting-pct','100_g_HAspread_for_personal-fouls-per-game','-50_g_HAspread_allow_points-per-game`/`possessions-per-game','-25_g_HAspread_allow_points-per-game`/`possessions-per-game','-30_g_HAspread_for_offensive-efficiency','-75_g_HAspread_allow_floor-percentage','pregame_ppp_for','-lightgbm_team','expected_ftm-per-100-possessions_for'],
                'model': KerasRegressor(build_fn=share_nn, epochs=270, batch_size=64, verbose=1),
                'scale': StandardScaler(),
                },
        },
        'winner':{
                '+pts':{
                    'log': {
                        'features': ['-lightgbm_team', '+lightgbm_target', '+linsvm_team', '+ridge_target', '+linsvm_all', '-lasso_possessions', '-ridge_all', '-linsvm_team', '-lightgbm_possessions', '-lightgbm_all', '-ridge_team', '-ridge_possessions', '+lasso_target', '-lightgbm_target', '-lasso_target', '+linsvm_target', '+ridge_all', '-lasso_team', '+lightgbm_team'],
                        'model': LogisticRegression(random_state = 1108, C = 1000, solver = "liblinear"),
                        'scale': StandardScaler(),
                        'acc_weight': 0.0584245954,
                        'logloss_weight': 0.1132769581,
                        'combined_weight': 0.0858507767,
                        },
                    },
                'raw':{
                    'knn': {
                        'features': ['-50_g_HAspread_for_personal-fouls-per-game', 'pregame_turnovers-per-possession_for', '-50_g_HAspread_for_assist--per--turnover-ratio', '75_g_HAspread_allow_points-per-game', '-10_g_HAspread_allow_ftm-per-100-possessions', 'expected_ppp_for', '-50_game_avg_30_g_Tweight_allow_fta-per-fga', '-100_g_HAspread_allow_assist--per--turnover-ratio', 'expected_turnovers-per-possession_for', '-75_g_HAspread_allow_defensive-efficiency', '-50_g_HAspread_allow_points-per-game`/`possessions-per-game', '75_g_HAspread_for_defensive-efficiency', '100_g_HAspread_for_personal-fouls-per-game', '30_g_HAspread_for_floor-percentage', '-100_g_HAspread_for_defensive-efficiency', '50_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_offensive-rebounding-pct_for', '100_g_HAspread_for_defensive-efficiency', '30_g_HAspread_allow_free-throw-rate', '-75_g_HAspread_allow_floor-percentage'],
                        'model': KNeighborsClassifier(n_neighbors = 166, leaf_size = 14),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.094108854,
                        'logloss_weight':0.1591595226, 
                        'combined_weight': 0.1266341883,
                        },                            
                    'log': {
                        'features': ['-10_g_HAspread_allow_ftm-per-100-possessions', 'expected_ppp_for', '100_g_HAspread_for_defensive-efficiency', '-100_g_HAspread_allow_assist--per--turnover-ratio', '-50_g_HAspread_allow_points-per-game`/`possessions-per-game', '-50_g_HAspread_for_personal-fouls-per-game', '75_g_HAspread_for_defensive-efficiency', '100_g_HAspread_for_personal-fouls-per-game', '30_g_HAspread_for_floor-percentage', '-100_g_HAspread_for_defensive-efficiency', '50_g_HAspread_allow_defensive-efficiency', '30_g_HAspread_allow_free-throw-rate', 'expected_turnovers-per-possession_for', 'pregame_turnovers-per-possession_for', 'expected_effective-field-goal-pct_for', '-75_g_HAspread_allow_defensive-efficiency', '-50_g_HAspread_for_assist--per--turnover-ratio', '-75_g_HAspread_allow_floor-percentage', 'expected_ftm-per-100-possessions_for', 'expected_offensive-rebounding-pct_for', '75_g_HAspread_allow_points-per-game'],
                        'model': LogisticRegression(random_state = 1108, C = 1.007409512406823, solver = "lbfgs"),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.2800316853,
                        'logloss_weight':0.2399684964, 
                        'combined_weight': 0.2600000908,
                        }, 
                    'linsvc': {
                        'features': ['-50_g_HAspread_for_personal-fouls-per-game', 'pregame_turnovers-per-possession_for', '-50_g_HAspread_for_assist--per--turnover-ratio', '75_g_HAspread_allow_points-per-game', '-10_g_HAspread_allow_ftm-per-100-possessions', 'expected_ppp_for', '-50_game_avg_30_g_Tweight_allow_fta-per-fga', '-100_g_HAspread_allow_assist--per--turnover-ratio', '-20_game_avg_50_g_Tweight_for_floor-percentage', 'expected_turnovers-per-possession_for', '-75_g_HAspread_allow_defensive-efficiency', '-50_g_HAspread_allow_points-per-game`/`possessions-per-game', '75_g_HAspread_for_defensive-efficiency', '100_g_HAspread_for_personal-fouls-per-game', '30_g_HAspread_for_floor-percentage', '-100_g_HAspread_for_defensive-efficiency', '50_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_offensive-rebounding-pct_for', '100_g_HAspread_for_defensive-efficiency', '30_g_HAspread_allow_free-throw-rate', '-75_g_HAspread_allow_floor-percentage'],
                        'model': SVC(random_state = 1108, C = 0.0207173498763, kernel = 'linear', probability = True),
                        'scale': StandardScaler(),
                        'acc_weight': 0.2778671236,
                        'logloss_weight':0.2364422815,  
                        'combined_weight': 0.2571547026,
                        }, 
                    'lightgbc': {
                        'features': ['-50_g_HAspread_for_personal-fouls-per-game', 'pregame_turnovers-per-possession_for', '-50_g_HAspread_for_assist--per--turnover-ratio', '75_g_HAspread_allow_points-per-game', '-10_g_HAspread_allow_ftm-per-100-possessions', 'expected_ppp_for', '-50_game_avg_30_g_Tweight_allow_fta-per-fga', '-100_g_HAspread_allow_assist--per--turnover-ratio', '-20_game_avg_50_g_Tweight_for_floor-percentage', 'expected_turnovers-per-possession_for', '-75_g_HAspread_allow_defensive-efficiency', '-50_g_HAspread_allow_points-per-game`/`possessions-per-game', '100_g_HAspread_for_personal-fouls-per-game', '75_g_HAspread_for_defensive-efficiency', '30_g_HAspread_for_floor-percentage', '-100_g_HAspread_for_defensive-efficiency', '50_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_offensive-rebounding-pct_for', '100_g_HAspread_for_defensive-efficiency', '30_g_HAspread_allow_free-throw-rate', '-75_g_HAspread_allow_floor-percentage'],
                        'model': lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, colsample_bytree = 0.642120736080607, min_child_samples = 116, num_leaves = 12, subsample = 0.897114330960264, max_bin = 1021, learning_rate = 0.08),
                        'scale': StandardScaler(), 
                        'acc_weight': 0.2895677417,
                        'logloss_weight':0.2511527414, 
                        'combined_weight': 0.2703602415,
                        },
                    'keras':{
                        'features': ['expected_ppp_for','expected_effective-field-goal-pct_for','50_g_HAspread_allow_defensive-efficiency','expected_offensive-rebounding-pct_for','-20_game_avg_50_g_Tweight_for_floor-percentage','100_g_HAspread_for_personal-fouls-per-game','-100_g_HAspread_allow_assist--per--turnover-ratio','expected_turnovers-per-possession_for','30_g_HAspread_allow_free-throw-rate','-100_g_HAspread_for_defensive-efficiency','pregame_turnovers-per-possession_for','-50_g_HAspread_for_personal-fouls-per-game','75_g_HAspread_for_defensive-efficiency','100_g_HAspread_for_defensive-efficiency','75_g_HAspread_allow_points-per-game','-75_g_HAspread_allow_floor-percentage','30_g_HAspread_for_floor-percentage','expected_ftm-per-100-possessions_for','-75_g_HAspread_allow_defensive-efficiency','-50_g_HAspread_allow_points-per-game`/`possessions-per-game','-50_game_avg_30_g_Tweight_allow_fta-per-fga','-50_g_HAspread_for_assist--per--turnover-ratio','-10_g_HAspread_allow_ftm-per-100-possessions'],
                        'model': KerasClassifier(build_fn=winner_nn, epochs=120, batch_size=16, verbose=1),
                        'scale': RobustScaler(),
                        'acc_weight': 0,
                        'logloss_weight': 0,
                        'combined_weight': 0,
                         },  
                },
        },
        'ou':{
                '+pts':{      
                    'log': {
                        'features': ['-ridge_team', '+lasso_target', '-linsvm_team', '+lightgbm_target', '+linsvm_all', '-lasso_possessions', '+rest', '-lightgbm_team', '+ridge_target', '+lightgbm_possessions', '-ridge_all', '-lasso_target', '+ridge_all', '+lightgbm_team', '+linsvm_team', '+lasso_possessions', '+linsvm_possessions', '-ridge_possessions', '-lightgbm_possessions', '-lightgbm_all', '-lightgbm_target', '+linsvm_target', '-lasso_team'],
                        'model':  LogisticRegression(random_state = 1108, C = 15.56187413425767, solver = "newton-cg"),
                        'scale' : MinMaxScaler(),
                        'acc_weight': 0.1248750836,
                        'logloss_weight':0.1463453962, 
                        'combined_weight': 0.1356102399,
                        }, 
                    'linsvc': {
                        'features': ['ridge_ou', '-ridge_team', '+lasso_target', '-linsvm_team', '+lightgbm_target', '+linsvm_all', '-lasso_possessions', '+rest', 'lightgbm_ou', '-lightgbm_team', '+ridge_target', '+lightgbm_possessions', '-ridge_all', 'pca_ou', '-lasso_target', '-rest', '+ridge_all', '+lightgbm_team', '+linsvm_team', '+lasso_possessions', '+linsvm_possessions', '-ridge_possessions', '-lightgbm_possessions', '-lightgbm_all', 'tsvd_ou', '-lightgbm_target', '+linsvm_target', '-lasso_team'],
                        'model': SVC(random_state = 1108, C =  0.15817437173, kernel = 'linear', probability = True),
                        'scale': MinMaxScaler(),
                        'acc_weight':0.0832124165,
                        'logloss_weight':0.134991219, 
                        'combined_weight': 0.1091018178,
                        },    
                    'lightgbc': {
                        'features': ['ridge_ou', 'lasso_ou', '-ridge_team', '+lasso_target', '-linsvm_team', '+lightgbm_target', '+linsvm_all', '-lasso_possessions', 'lightgbm_ou', '+rest', '-lightgbm_team', '+ridge_target', '+lightgbm_possessions', '-ridge_all', 'pca_ou', '-lasso_target', '-rest', '+ridge_all', '+lightgbm_team', '+linsvm_team', '+lasso_possessions', '+linsvm_possessions', '-ridge_possessions', '-lightgbm_possessions', '-lightgbm_all', 'tsvd_ou', '-lightgbm_target', '+linsvm_target', '-lasso_team'],
                        'model': lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, colsample_bytree = 0.925424645171526, min_child_samples = 63, num_leaves = 159, subsample = 0.417196512684593, max_bin = 1011, learning_rate = 0.01),
                        'scale': StandardScaler(),
                        'acc_weight': 0.0779914282,
                        'logloss_weight':0.1290890707, 
                        'combined_weight': 0.1035402494,
                        },                                          
                },
                'raw':{
                    'lightgbc': {
                        'features': ['-50_game_avg_50_g_HAweight_allow_ftm-per-100-possessions', 'ridge_ou', '-30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game', 'lasso_ou', '20_game_avg_30_g_HAweight_for_defensive-rebounds-per-game', '10_game_avg_50_g_HAweight_for_blocks-per-game', '100_g_HAspread_allow_block-pct', '-1_game_avg_10_g_Tweight_allow_possessions-per-game', '-20_game_avg_50_g_HAweight_allow_defensive-efficiency', '-20_game_avg_50_g_Tweight_for_floor-percentage', '-100_g_HAspread_allow_assist--per--turnover-ratio', '-100_g_HAspread_for_points-per-game', '-expected_effective-field-goal-pct_allowed', '-10_game_avg_10_g_HAweight_allow_points-per-game', '-10_game_avg_15_g_HAweight_for_defensive-efficiency', '-30_game_avg_50_g_HAweight_allow_points-per-game', '10_game_avg_30_g_Tweight_for_true-shooting-percentage', '-75_g_HAspread_allow_defensive-efficiency', 'lightgbm_ou', '30_game_avg_5_g_Tweight_for_possessions-per-game', '25_g_HAspread_for_points-per-game', '-50_game_avg_50_g_HAweight_for_assists-per-game', 'pca_ou', '-15_g_HAspread_allow_block-pct', 'expected_effective-field-goal-pct_for', '20_game_avg_10_g_HAweight_for_possessions-per-game', '-30_game_avg_25_g_Tweight_allow_points-per-game', '-20_game_avg_50_g_Tweight_allow_points-per-game', '50_game_avg_50_g_HAweight_for_assists-per-game', '-10_game_avg_10_g_Tweight_allow_points-per-game`/`possessions-per-game', '75_g_HAspread_for_floor-percentage', '-10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game', '10_game_avg_10_g_Tweight_for_possessions-per-game', '75_g_HAspread_allow_percent-of-points-from-3-pointers', 'tsvd_ou', '-25_g_HAspread_allow_possessions-per-game', '25_g_HAspread_for_possessions-per-game'],
                        'model': lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, colsample_bytree = 0.785582982952984, min_child_samples = 198, num_leaves = 11, subsample = 0.633073504349269, max_bin = 1359, learning_rate = 0.02),
                        'scale': StandardScaler(),
                        'acc_weight': 0.1484550049,
                        'logloss_weight':0.1404922534, 
                        'combined_weight': 0.1444736291,
                        },
                    'knn': {
                        'features': ['-50_game_avg_50_g_HAweight_allow_ftm-per-100-possessions', '-30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game', 'ridge_ou', 'lasso_ou', '20_game_avg_30_g_HAweight_for_defensive-rebounds-per-game', '10_game_avg_50_g_HAweight_for_blocks-per-game', '100_g_HAspread_allow_block-pct', '-20_game_avg_50_g_HAweight_allow_defensive-efficiency', '-20_game_avg_50_g_Tweight_for_floor-percentage', '-100_g_HAspread_allow_assist--per--turnover-ratio', '-100_g_HAspread_for_points-per-game', '-expected_effective-field-goal-pct_allowed', '-10_game_avg_10_g_HAweight_allow_points-per-game', '-10_game_avg_15_g_HAweight_for_defensive-efficiency', '-30_game_avg_50_g_HAweight_allow_points-per-game', '10_game_avg_30_g_Tweight_for_true-shooting-percentage', '-75_g_HAspread_allow_defensive-efficiency', 'lightgbm_ou', '30_game_avg_5_g_Tweight_for_possessions-per-game', '25_g_HAspread_for_points-per-game', '-50_game_avg_50_g_HAweight_for_assists-per-game', 'pca_ou', 'expected_effective-field-goal-pct_for', '20_game_avg_10_g_HAweight_for_possessions-per-game', '-30_game_avg_25_g_Tweight_allow_points-per-game', '-20_game_avg_50_g_Tweight_allow_points-per-game', '50_game_avg_50_g_HAweight_for_assists-per-game', '-10_game_avg_10_g_Tweight_allow_points-per-game`/`possessions-per-game', '75_g_HAspread_for_floor-percentage', '-20_game_avg_25_g_Tweight_allow_possessions-per-game', '-10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game', '10_game_avg_10_g_Tweight_for_possessions-per-game', '75_g_HAspread_allow_percent-of-points-from-3-pointers', 'tsvd_ou', '25_g_HAspread_for_possessions-per-game', '-25_g_HAspread_allow_possessions-per-game', '-15_g_HAspread_allow_block-pct'],
                        'model': KNeighborsClassifier(n_neighbors = 88, leaf_size = 30),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.1910461882,
                        'logloss_weight':0.1667201587,
                        'combined_weight': 0.1788831735,
                        },                            
                    'log': {
                        'features': ['-10_game_avg_10_g_Tweight_allow_points-per-game`/`possessions-per-game', '-20_game_avg_50_g_Tweight_for_floor-percentage', '30_game_avg_5_g_Tweight_for_possessions-per-game', '-100_g_HAspread_allow_assist--per--turnover-ratio', '25_g_HAspread_for_points-per-game', '-20_game_avg_25_g_Tweight_allow_possessions-per-game', '-expected_effective-field-goal-pct_allowed', '-10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game', '10_game_avg_10_g_Tweight_for_possessions-per-game', '20_game_avg_30_g_HAweight_for_defensive-rebounds-per-game', '-10_game_avg_15_g_HAweight_for_defensive-efficiency', '-10_game_avg_10_g_HAweight_allow_points-per-game', '75_g_HAspread_allow_percent-of-points-from-3-pointers', 'expected_effective-field-goal-pct_for', '10_game_avg_30_g_Tweight_for_true-shooting-percentage', '20_game_avg_10_g_HAweight_for_possessions-per-game', '-20_game_avg_50_g_Tweight_allow_points-per-game', '-20_game_avg_50_g_HAweight_allow_defensive-efficiency'],
                        'model':LogisticRegression(random_state = 1108, C = 0.04795626933077879, solver = "liblinear"),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.1910461882,
                        'logloss_weight':0.1465037713,
                        'combined_weight': 0.1687749798,
                        }, 
                    'keras':{
                        'features': ['expected_effective-field-goal-pct_for','10_game_avg_30_g_Tweight_for_true-shooting-percentage','-75_g_HAspread_allow_defensive-efficiency','100_g_HAspread_allow_block-pct','10_game_avg_10_g_Tweight_for_possessions-per-game','-expected_effective-field-goal-pct_allowed','75_g_HAspread_for_floor-percentage','-10_game_avg_15_g_HAweight_for_defensive-efficiency','-30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game','30_game_avg_5_g_Tweight_for_possessions-per-game','25_g_HAspread_for_points-per-game','-30_game_avg_50_g_HAweight_allow_points-per-game','-10_game_avg_10_g_Tweight_allow_points-per-game`/`possessions-per-game','-1_game_avg_10_g_Tweight_allow_possessions-per-game','-100_g_HAspread_for_points-per-game','-50_game_avg_50_g_HAweight_for_assists-per-game','25_g_HAspread_for_possessions-per-game','10_game_avg_50_g_HAweight_for_blocks-per-game','-50_game_avg_50_g_HAweight_allow_ftm-per-100-possessions','20_game_avg_30_g_HAweight_for_defensive-rebounds-per-game','-20_game_avg_50_g_Tweight_for_floor-percentage','20_game_avg_10_g_HAweight_for_possessions-per-game','-20_game_avg_50_g_Tweight_allow_points-per-game','-100_g_HAspread_allow_assist--per--turnover-ratio','-10_game_avg_10_g_HAweight_allow_points-per-game','75_g_HAspread_allow_percent-of-points-from-3-pointers','-15_g_HAspread_allow_block-pct','-20_game_avg_25_g_Tweight_allow_possessions-per-game','-10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game','-20_game_avg_50_g_HAweight_allow_defensive-efficiency','50_game_avg_50_g_HAweight_for_assists-per-game','-30_game_avg_25_g_Tweight_allow_points-per-game','-25_g_HAspread_allow_possessions-per-game', 'pca_ou', 'tsvd_ou', 'lasso_ou', 'lightgbm_ou', 'ridge_ou', 'vegas_ou'],
                        'model': KerasClassifier(build_fn=ou_nn, epochs=120, batch_size=16, verbose=1),
                        'scale': StandardScaler(),
                        'acc_weight': 0.1833736905,
                        'logloss_weight': 0.1358581306,
                        'combined_weight': 0.1596159105,
                         },  
                },
        },
        'line':{
                '+pts':{
                    'knn': {
                        'features': ['lasso_line'],
                        'model': KNeighborsClassifier(n_neighbors = 198, leaf_size = 100),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.0825221487,
                        'logloss_weight':0.1066648644, 
                        'combined_weight': 0.0945935065,
                        },       
                    'log': {
                        'features': ['+ridge_target', 'ridge_line', 'lasso_line', '-ridge_team', '+lasso_target', '-lasso_target', '+linsvm_target', 'lightgbm_line', '-lasso_team'],
                        'model': LogisticRegression(random_state = 1108, C = 13.48854758964598, solver = "liblinear"),
                        'scale': RobustScaler(),
                        'acc_weight': 0.1525401044,
                        'logloss_weight':0.1475158118,
                        'combined_weight': 0.1500279581,
                        },                                              
                    'linsvc': {
                        'features': ['+ridge_target', 'ridge_line', 'lasso_line', '-ridge_team', '+lasso_target', '+linsvm_target', 'lightgbm_line', '-lasso_team'],
                        'model': SVC(random_state = 1108, C =  4.87778133978, kernel = 'linear', probability = True),
                        'scale': StandardScaler(),
                        'acc_weight': 0.1170752145,
                        'logloss_weight':0.1454490533,
                        'combined_weight': 0.1312621339,
                        }, 
                    'lightgbc': {
                        'features': ['+linsvm_team', '+ridge_target', '+lasso_possessions', '+linsvm_possessions', '+linsvm_all', '-ridge_possessions', 'lasso_line', '-lasso_target', '-lasso_possessions', 'tsvd_line', 'pca_line', 'lightgbm_line', '-lasso_team'],
                        'model': lgb.LGBMClassifier(random_state = 1108, n_estimators = 225, colsample_bytree =0.985094185628027, min_child_samples = 13, num_leaves = 15, subsample = 0.721806428713343, max_bin = 1110, learning_rate = 0.03),
                        'scale': RobustScaler(),
                        'acc_weight': 0.183227768,
                        'logloss_weight':0.155520103, 
                        'combined_weight': 0.1693739355,
                        },                                             
            },
                'raw':{
                    'lightgbc': {
                        'features': ['pregame_ppp_for', 'ridge_line', '50_game_avg_50_g_HAweight_for_defensive-rebounding-pct', '-5_game_avg_50_g_HAweight_allow_possessions-per-game', '100_g_HAspread_allow_block-pct', '-50_game_avg_30_g_Tweight_allow_block-pct', '-expected_effective-field-goal-pct_allowed', '-75_g_HAspread_allow_defensive-efficiency', '-20_game_avg_15_g_Tweight_allow_extra-chances-per-game', 'lasso_line', '-20_game_avg_50_g_Tweight_for_block-pct', '1_game_avg_10_g_HAweight_for_points-per-game', '75_g_HAspread_for_defensive-efficiency', '50_game_avg_30_g_Tweight_allow_offensive-efficiency', '20_game_avg_30_g_HAweight_allow_fta-per-fga', '-50_game_avg_50_g_HAweight_for_offensive-rebounding-pct', '-5_game_avg_10_g_Tweight_allow_possessions-per-game', 'pca_line', 'tsvd_line', '-10_game_avg_50_g_Tweight_for_assists-per-game', '-30_game_avg_10_g_HAweight_allow_possessions-per-game', '10_game_avg_30_g_Tweight_for_assists-per-game', '-20_game_avg_50_g_Tweight_allow_fta-per-fga', '100_g_HAspread_for_defensive-efficiency', '50_g_HAspread_allow_assist--per--turnover-ratio', '20_game_avg_30_g_Tweight_allow_assist--per--turnover-ratio', '75_g_HAspread_allow_defensive-efficiency', '-50_game_avg_15_g_Tweight_allow_blocks-per-game', '-50_game_avg_50_g_Tweight_for_assist--per--turnover-ratio', 'pregame_offensive-rebounding-pct_for', '-50_game_avg_15_g_HAweight_allow_blocks-per-game', '-expected_poss_pg_allowed', 'lightgbm_line', '25_g_HAspread_for_possessions-per-game'],
                        'model': lgb.LGBMClassifier(random_state = 1108, n_estimators = 150, colsample_bytree = 0.609201056258738, min_child_samples = 177, num_leaves = 49, subsample = 0.814351700300212, max_bin = 1958, learning_rate = 0.005),
                        'scale': MinMaxScaler(),
                        'acc_weight': 0.2121008537,
                        'logloss_weight':0.1561942556,
                        'combined_weight': 0.1841475546,                         
                        },                          
                    'log': {
                        'features': ['ridge_line', 'lasso_line', 'lightgbm_line'],
                        'model': LogisticRegression(random_state = 1108, C = 0.012407087605742084, solver = "liblinear"),
                        'scale': RobustScaler(),
                        'acc_weight': 0.1143462307,
                        'logloss_weight':0.1474005668,   
                        'combined_weight': 0.1308733987,
                        }, 
                    'keras':{
                        'features': ['20_game_avg_30_g_HAweight_allow_fta-per-fga','-75_g_HAspread_allow_defensive-efficiency','-expected_poss_pg_allowed','50_game_avg_50_g_HAweight_for_defensive-rebounding-pct','75_g_HAspread_allow_defensive-efficiency','-20_game_avg_50_g_Tweight_allow_fta-per-fga','50_g_HAspread_allow_assist--per--turnover-ratio','50_game_avg_30_g_Tweight_allow_offensive-efficiency','-50_game_avg_15_g_HAweight_allow_blocks-per-game','pregame_offensive-rebounding-pct_for','10_game_avg_30_g_Tweight_for_assists-per-game','20_game_avg_30_g_Tweight_allow_assist--per--turnover-ratio','-30_game_avg_10_g_HAweight_allow_possessions-per-game','-50_game_avg_50_g_Tweight_for_assist--per--turnover-ratio','100_g_HAspread_allow_block-pct','75_g_HAspread_for_defensive-efficiency','1_game_avg_10_g_HAweight_for_points-per-game','-50_game_avg_30_g_Tweight_allow_block-pct','25_g_HAspread_for_possessions-per-game','-5_game_avg_10_g_Tweight_allow_possessions-per-game','100_g_HAspread_for_defensive-efficiency','-10_game_avg_50_g_Tweight_for_assists-per-game','-20_game_avg_15_g_Tweight_allow_extra-chances-per-game','pregame_ppp_for','-expected_effective-field-goal-pct_allowed','-5_game_avg_50_g_HAweight_allow_possessions-per-game','-10_g_HAspread_allow_points-per-game`/`possessions-per-game','-50_game_avg_15_g_Tweight_allow_blocks-per-game','-50_game_avg_50_g_HAweight_for_offensive-rebounding-pct','-20_game_avg_50_g_Tweight_for_block-pct', 'pca_line', 'tsvd_line', 'lasso_line', 'lightgbm_line', 'ridge_line', 'vegas_line'],
                        'model': KerasClassifier(build_fn=line_nn, epochs=30, batch_size=64, verbose=1),
                        'scale': StandardScaler(),
                        'acc_weight': 0.13818768,
                        'logloss_weight': 0.1412553452,
                        'combined_weight': 0.1397215126,
                         },  
                },
        },
        'result':{
                'line':{
                    'ridge': {
                        'features': ['10_game_avg', 'ha', 'streak'],
                        'model': Ridge(random_state = 1108, solver = 'sag', alpha = 584.39992591),
                        'scale' : MinMaxScaler(),
                        },
                    'lasso': {
                        'features': ['10_game_avg', 'ha', 'streak'],
                        'model': Lasso(random_state = 1108, alpha = 0.0011089952827, max_iter = 2000),
                        'scale': StandardScaler(),
                        },
                    'lightgbm': {
                        'features': ['10_game_avg', 'ha', 'streak', '50_game_avg'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 1000, colsample_bytree = 0.980189782695348, min_child_samples = 189, num_leaves = 14, subsample = 0.791883150188403, max_bin = 1988, learning_rate = 0.00140625),
                        'scale': StandardScaler(), 
                        }
                },
                'ou': {
                    'ridge': {
                        'features': ['10_game_avg', '50_game_avg', '15_game_avg', '30_game_avg', 'streak', '5_game_avg'],
                        'model': Ridge(random_state = 1108, solver = 'lsqr', alpha = 737.480281596),
                        'scale': MinMaxScaler(),
                        },
                    'lasso': {
                        'features': ['10_game_avg', '50_game_avg', '15_game_avg', '30_game_avg', 'streak', '5_game_avg'],
                        'model': Lasso(random_state = 1108, alpha = 0.00171909758817),
                        'scale': StandardScaler(),
                        },
                    'lightgbm': {
                        'features': ['10_game_avg', '15_game_avg', '50_game_avg', '30_game_avg', 'streak', '5_game_avg', '3_game_avg'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 300, colsample_bytree = 0.952264164385702, min_child_samples = 12, num_leaves = 36, subsample = 0.64633747168907, max_bin = 1138, learning_rate = 0.015),                
                        'scale': StandardScaler(),
                }
            },
        },
        'pts_allowed': {
                'all': {
                    'ridge': {
                        'features': ['expected_poss_pg_allowed', '25_g_HAspread_allow_possessions-per-game', '20_game_avg_50_g_Tweight_for_defensive-efficiency', 'expected_turnovers-per-possession_allowed', 'pregame_turnovers-per-possession_allowed', '10_game_avg_50_g_Tweight_for_assists-per-game', '30_game_avg_10_g_HAweight_allow_possessions-per-game', '100_g_HAspread_for_defensive-efficiency', 'pregame_pts_pg_allowed', '30_game_avg_25_g_Tweight_allow_points-per-game', 'expected_offensive-rebounding-pct_allowed', 'pregame_ftm-per-100-possessions_allowed', '50_game_avg_50_g_HAweight_for_assists-per-game', 'pregame_ppp_allowed', '10_g_HAspread_allow_points-per-game`/`possessions-per-game', '10_game_avg_10_g_HAweight_allow_points-per-game', 'expected_ppp_allowed', '75_g_HAspread_allow_floor-percentage', '10_game_avg_50_g_Tweight_allow_offensive-rebounding-pct', '20_game_avg_30_g_HAweight_for_ftm-per-100-possessions', '50_g_HAspread_for_assist--per--turnover-ratio', '50_game_avg_30_g_HAweight_allow_defensive-rebounds-per-game', 'expected_effective-field-goal-pct_allowed', '10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game', '50_game_avg_30_g_Tweight_allow_fta-per-fga', 'expected_pts_pg_allowed'],
                        'model': Ridge(random_state = 1108, solver = 'sparse_cg', alpha = 0.89393381144),
                        'scale': MinMaxScaler(),
                        },
                    'lightgbm': {
                        'features': ['expected_poss_pg_allowed', '25_g_HAspread_allow_possessions-per-game', '20_game_avg_50_g_Tweight_for_defensive-efficiency', 'pregame_turnovers-per-possession_allowed', 'expected_turnovers-per-possession_allowed', '10_game_avg_50_g_Tweight_for_assists-per-game', '30_game_avg_10_g_HAweight_allow_possessions-per-game', '100_g_HAspread_for_defensive-efficiency', 'pregame_pts_pg_allowed', '30_game_avg_25_g_Tweight_allow_points-per-game', '50_game_avg_50_g_HAweight_for_assists-per-game', 'pregame_ftm-per-100-possessions_allowed', 'expected_offensive-rebounding-pct_allowed', 'pregame_ppp_allowed', '10_g_HAspread_allow_points-per-game`/`possessions-per-game', '10_game_avg_10_g_HAweight_allow_points-per-game', 'expected_ppp_allowed', '75_g_HAspread_allow_floor-percentage', '10_game_avg_50_g_Tweight_allow_offensive-rebounding-pct', '20_game_avg_30_g_HAweight_for_ftm-per-100-possessions', '50_g_HAspread_for_assist--per--turnover-ratio', '50_game_avg_30_g_HAweight_allow_defensive-rebounds-per-game', 'expected_effective-field-goal-pct_allowed', '10_game_avg_15_g_HAweight_allow_defensive-rebounds-per-game', '50_game_avg_30_g_Tweight_allow_fta-per-fga', 'expected_pts_pg_allowed'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 400, colsample_bytree = 0.796359005305649, min_child_samples = 198, num_leaves = 13, subsample = 0.65344498465166, max_bin = 1953, learning_rate = 0.03),
                        'scale': StandardScaler(),
                        }
                    },
                'target':{
                    'lightgbm': {
                        'features': ['expected_ppp_allowed', '20_game_avg_25_g_Tweight_allow_points-per-game', '50_g_HAspread_allow_points-per-game`/`possessions-per-game', '10_game_avg_5_g_Tweight_allow_points-per-game`/`possessions-per-game', '30_game_avg_25_g_Tweight_allow_points-per-game', '1_game_avg_25_g_Tweight_allow_points-per-game`/`possessions-per-game', '10_game_avg_25_g_HAweight_allow_points-per-game', '20_game_avg_50_g_Tweight_allow_points-per-game', '25_g_HAspread_allow_points-per-game`/`possessions-per-game', 'pregame_ppp_allowed', '30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game', 'expected_pts_pg_allowed', '10_g_HAspread_allow_points-per-game`/`possessions-per-game'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 900, colsample_bytree = 0.956416580127077, min_child_samples = 4, num_leaves = 61, subsample = 0.631441132669909, max_bin = 1974, learning_rate = 0.00375),
                        'scale': MinMaxScaler(),
                        },                         
                    'lasso': {
                        'features': ['expected_ppp_allowed', '20_game_avg_25_g_Tweight_allow_points-per-game', '50_g_HAspread_allow_points-per-game`/`possessions-per-game', '10_game_avg_5_g_Tweight_allow_points-per-game`/`possessions-per-game', '30_game_avg_25_g_Tweight_allow_points-per-game', '1_game_avg_25_g_Tweight_allow_points-per-game`/`possessions-per-game', '10_game_avg_25_g_HAweight_allow_points-per-game', '20_game_avg_5_g_HAweight_allow_points-per-game', '20_game_avg_50_g_Tweight_allow_points-per-game', '25_g_HAspread_allow_points-per-game`/`possessions-per-game', 'pregame_ppp_allowed', '30_game_avg_50_g_Tweight_allow_points-per-game`/`possessions-per-game', 'expected_pts_pg_allowed', '10_g_HAspread_allow_points-per-game`/`possessions-per-game'],
                        'model': Lasso(random_state = 1108, alpha = 0.001, max_iter = 2000),
                        'scale': StandardScaler(),
                        },
                    },
                'possessions': {
                    'lightgbm': {
                        'features': ['expected_poss_pg_allowed', '1_game_avg_50_g_HAweight_allow_possessions-per-game', 'pregame_poss_pg_allowed', '5_game_avg_25_g_Tweight_allow_possessions-per-game', '25_g_HAspread_allow_possessions-per-game', '5_game_avg_10_g_Tweight_allow_possessions-per-game', '30_game_avg_5_g_Tweight_allow_possessions-per-game', '1_game_avg_10_g_Tweight_allow_possessions-per-game', '20_game_avg_50_g_Tweight_allow_possessions-per-game', '30_game_avg_25_g_HAweight_allow_possessions-per-game'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 4050, colsample_bytree = 0.947978555103353, min_child_samples = 4, num_leaves = 20, subsample = 0.417125690980936, max_bin = 1114, learning_rate = 0.00125),
                        'scale': StandardScaler(),
                        },
                    'ridge': {
                        'features': ['expected_poss_pg_allowed', '1_game_avg_50_g_HAweight_allow_possessions-per-game', 'pregame_poss_pg_allowed', '5_game_avg_25_g_Tweight_allow_possessions-per-game', '25_g_HAspread_allow_possessions-per-game', '5_game_avg_10_g_Tweight_allow_possessions-per-game', '1_game_avg_10_g_Tweight_allow_possessions-per-game', '20_game_avg_50_g_Tweight_allow_possessions-per-game', '30_game_avg_25_g_HAweight_allow_possessions-per-game'],
                        'model': Ridge(random_state = 1108, solver = 'lsqr', alpha = 4.095337845324041),
                        'scale': MinMaxScaler(),
                        }, 
                    'lasso': {
                        'features': ['expected_poss_pg_allowed', '1_game_avg_50_g_HAweight_allow_possessions-per-game', 'pregame_poss_pg_allowed', '5_game_avg_25_g_Tweight_allow_possessions-per-game', '25_g_HAspread_allow_possessions-per-game', '5_game_avg_10_g_Tweight_allow_possessions-per-game', '1_game_avg_10_g_Tweight_allow_possessions-per-game', '30_game_avg_5_g_Tweight_allow_possessions-per-game', '20_game_avg_50_g_Tweight_allow_possessions-per-game', '30_game_avg_25_g_HAweight_allow_possessions-per-game'],
                        'model': Lasso(random_state = 1108, alpha = 0.001),
                        'scale': RobustScaler(),
                        },
                    },
                'full-team':{
                    'linsvm': {
                        'features': ['50_g_HAspread_for_assist--per--turnover-ratio', '100_g_HAspread_for_defensive-efficiency', '75_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_allowed', '75_g_HAspread_allow_floor-percentage', 'expected_turnovers-per-possession_allowed', 'expected_offensive-rebounding-pct_allowed', '100_g_HAspread_allow_assist--per--turnover-ratio', '30_g_HAspread_for_offensive-efficiency'],
                        'model': LinearSVR(random_state = 1108, C = 2.45976772084, epsilon=0),
                        'scale': MinMaxScaler(),
                        }, 
                    'ridge': {
                        'features': ['50_g_HAspread_for_assist--per--turnover-ratio', '100_g_HAspread_for_defensive-efficiency', '75_g_HAspread_allow_defensive-efficiency', 'pregame_offensive-rebounding-pct_allowed', 'expected_effective-field-goal-pct_allowed', '75_g_HAspread_allow_floor-percentage', 'expected_turnovers-per-possession_allowed', 'pregame_turnovers-per-possession_allowed', 'expected_offensive-rebounding-pct_allowed', '100_g_HAspread_for_points-per-game', '100_g_HAspread_allow_assist--per--turnover-ratio', '30_g_HAspread_for_offensive-efficiency'],
                        'model': Ridge(random_state = 1108, solver = 'lsqr', alpha = 6.07138889187),
                        'scale': MinMaxScaler(),
                        },  
                    'lasso': {
                        'features': ['50_g_HAspread_for_assist--per--turnover-ratio', '100_g_HAspread_for_defensive-efficiency', '75_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_allowed', '75_g_HAspread_allow_floor-percentage', 'expected_turnovers-per-possession_allowed', 'expected_offensive-rebounding-pct_allowed', '100_g_HAspread_for_points-per-game', '100_g_HAspread_allow_assist--per--turnover-ratio', '30_g_HAspread_for_offensive-efficiency'],
                        'model': Lasso(random_state = 1108, alpha = 0.00125925622966, max_iter = 2000),
                        'scale': RobustScaler(),
                        },
                    'lightgbm': {
                        'features': ['30_g_HAspread_for_offensive-efficiency', '50_g_HAspread_for_assist--per--turnover-ratio', '100_g_HAspread_for_defensive-efficiency', 'pregame_offensive-rebounding-pct_allowed', '75_g_HAspread_allow_defensive-efficiency', 'expected_effective-field-goal-pct_allowed', '75_g_HAspread_allow_floor-percentage', 'pregame_turnovers-per-possession_allowed', 'expected_turnovers-per-possession_allowed', '100_g_HAspread_for_points-per-game', 'expected_offensive-rebounding-pct_allowed', '100_g_HAspread_allow_assist--per--turnover-ratio', '50_game_avg_15_g_Tweight_allow_blocks-per-game', '20_game_avg_30_g_Tweight_for_defensive-rebounding-pct'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 1400, colsample_bytree = 0.99323664013058, min_child_samples = 61, num_leaves = 46, subsample = 0.464276892923476, max_bin = 1557, learning_rate = 0.0028125),
                        'scale': StandardScaler(),
                        }                            
                    }
                },
        'pts_scored': {
                'all':{
                    'linsvm': {
                        'features': ['expected_effective-field-goal-pct_for', '100_g_HAspread_for_floor-percentage', '75_g_HAspread_allow_percent-of-points-from-3-pointers', '50_game_avg_50_g_Tweight_for_personal-fouls-per-possession', 'expected_offensive-rebounding-pct_for', '50_g_HAspread_for_points-per-game', '10_g_HAspread_allow_personal-fouls-per-possession', '30_g_HAspread_allow_floor-percentage', 'expected_ftm-per-100-possessions_for', 'expected_turnovers-per-possession_for', '50_game_avg_30_g_Tweight_for_personal-fouls-per-possession', '10_game_avg_5_g_HAweight_for_points-per-game`/`possessions-per-game', '100_g_HAspread_allow_assist--per--turnover-ratio', '100_g_HAspread_allow_block-pct', 'expected_ppp_for', '75_g_HAspread_for_offensive-efficiency', 'expected_pts_pg_for', '75_g_HAspread_for_floor-percentage', 'expected_poss_pg_for', '25_g_HAspread_for_points-per-game', '30_g_HAspread_for_defensive-efficiency', '1_game_avg_50_g_HAweight_for_possessions-per-game', 'pregame_ppp_for', '50_game_avg_30_g_HAweight_allow_two-point-rate', 'pregame_pts_pg_for'],
                        'model': LinearSVR(random_state = 1108, C = 1.19681838901, epsilon=0),
                        'scale': MinMaxScaler(),
                        },
                    'ridge': {
                        'features': ['expected_effective-field-goal-pct_for', '100_g_HAspread_for_floor-percentage', '75_g_HAspread_allow_percent-of-points-from-3-pointers', '50_game_avg_50_g_Tweight_for_personal-fouls-per-possession', 'expected_offensive-rebounding-pct_for', '50_g_HAspread_for_points-per-game', '10_g_HAspread_allow_personal-fouls-per-possession', '30_g_HAspread_allow_floor-percentage', 'expected_ftm-per-100-possessions_for', 'expected_turnovers-per-possession_for', '50_game_avg_30_g_Tweight_for_personal-fouls-per-possession', '10_game_avg_5_g_HAweight_for_points-per-game`/`possessions-per-game', '100_g_HAspread_allow_assist--per--turnover-ratio', '100_g_HAspread_allow_block-pct', 'expected_ppp_for', '75_g_HAspread_for_offensive-efficiency', 'expected_pts_pg_for', '75_g_HAspread_for_floor-percentage', 'expected_poss_pg_for', '25_g_HAspread_for_points-per-game', '30_g_HAspread_for_defensive-efficiency', '1_game_avg_50_g_HAweight_for_possessions-per-game', 'pregame_ppp_for', '50_game_avg_30_g_HAweight_allow_two-point-rate', 'pregame_pts_pg_for'],
                        'model': Ridge(random_state = 1108, solver = 'lsqr', alpha = 0.00115411795019),
                        'scale': StandardScaler(),
                        },                                              
                    },
                'possessions':{
                    'linsvm': {
                        'features': ['30_game_avg_5_g_Tweight_for_possessions-per-game', '1_game_avg_50_g_Tweight_for_possessions-per-game', '20_game_avg_10_g_HAweight_for_possessions-per-game', '50_g_HAspread_for_possessions-per-game', 'pregame_poss_pg_for', '25_g_HAspread_for_possessions-per-game', '30_game_avg_50_g_HAweight_for_possessions-per-game', '1_game_avg_5_g_Tweight_for_possessions-per-game', '30_game_avg_10_g_Tweight_for_possessions-per-game', '10_game_avg_10_g_HAweight_for_possessions-per-game', 'expected_poss_pg_for', '10_game_avg_10_g_Tweight_for_possessions-per-game', '30_game_avg_25_g_Tweight_for_possessions-per-game'],
                        'model': LinearSVR(random_state = 1108, C = 2.7208908100107254, epsilon=0),
                        'scale': MinMaxScaler(),
                        },
                    'lightgbm': {
                        'features': ['30_game_avg_5_g_Tweight_for_possessions-per-game', '1_game_avg_50_g_Tweight_for_possessions-per-game', '20_game_avg_10_g_HAweight_for_possessions-per-game', 'pregame_poss_pg_for', '30_game_avg_50_g_HAweight_for_possessions-per-game', '1_game_avg_5_g_Tweight_for_possessions-per-game', '10_game_avg_10_g_HAweight_for_possessions-per-game', 'expected_poss_pg_for', '10_game_avg_10_g_Tweight_for_possessions-per-game', '30_game_avg_25_g_Tweight_for_possessions-per-game'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 2800, colsample_bytree = 0.961267241448647, min_child_samples = 9, num_leaves = 18, subsample = 0.596425797228693, max_bin = 1844, learning_rate = 0.0025),
                        'scale': MinMaxScaler(),
                        },
                    'lasso': {
                        'features': ['30_game_avg_5_g_Tweight_for_possessions-per-game', '1_game_avg_50_g_Tweight_for_possessions-per-game', '20_game_avg_10_g_HAweight_for_possessions-per-game', '50_g_HAspread_for_possessions-per-game', 'pregame_poss_pg_for', '25_g_HAspread_for_possessions-per-game', '30_game_avg_50_g_HAweight_for_possessions-per-game', '1_game_avg_5_g_Tweight_for_possessions-per-game', '30_game_avg_10_g_Tweight_for_possessions-per-game', '10_game_avg_10_g_HAweight_for_possessions-per-game', 'expected_poss_pg_for', '10_game_avg_10_g_Tweight_for_possessions-per-game', '30_game_avg_25_g_Tweight_for_possessions-per-game'],
                        'model': Lasso(random_state = 1108, alpha = 0.0015540696172751227, max_iter = 2000),
                        'scale': StandardScaler(),
                        },
                    },
                'target':{
                    'linsvm': {
                        'features': ['50_g_HAspread_for_points-per-game', '50_g_HAspread_for_points-per-game`/`possessions-per-game', 'pregame_ppp_for', '20_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', '10_game_avg_5_g_Tweight_for_points-per-game`/`possessions-per-game', 'expected_ppp_for', '25_g_HAspread_for_points-per-game`/`possessions-per-game', 'expected_pts_pg_for', '5_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', '1_game_avg_10_g_HAweight_for_points-per-game', 'pregame_pts_pg_for', '10_game_avg_5_g_HAweight_for_points-per-game`/`possessions-per-game'],
                        'model': LinearSVR(random_state = 1108, C = 0.12071774068337349, epsilon=0),
                        'scale': MinMaxScaler(),
                        },
                    'lightgbm': {
                        'features': ['50_g_HAspread_for_points-per-game', '50_g_HAspread_for_points-per-game`/`possessions-per-game', 'pregame_ppp_for', '20_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', '10_game_avg_5_g_Tweight_for_points-per-game`/`possessions-per-game', 'expected_ppp_for', '25_g_HAspread_for_points-per-game`/`possessions-per-game', 'expected_pts_pg_for', '5_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', '1_game_avg_10_g_HAweight_for_points-per-game', 'pregame_pts_pg_for', '10_game_avg_5_g_HAweight_for_points-per-game`/`possessions-per-game'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 500, colsample_bytree = 0.780673078959247, min_child_samples = 5, num_leaves = 17, subsample = 0.607386007072246, max_bin = 1307, learning_rate = 0.0075),
                        'scale': MinMaxScaler(),
                        },
                    'ridge': {
                        'features': ['50_g_HAspread_for_points-per-game', '50_g_HAspread_for_points-per-game`/`possessions-per-game', 'pregame_ppp_for', '20_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', '10_game_avg_5_g_Tweight_for_points-per-game`/`possessions-per-game', 'expected_ppp_for', '25_g_HAspread_for_points-per-game`/`possessions-per-game', 'expected_pts_pg_for', '5_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', 'pregame_pts_pg_for', '10_game_avg_5_g_HAweight_for_points-per-game`/`possessions-per-game'],
                        'model': Ridge(random_state = 1108, solver = 'sparse_cg', alpha = 0.5619646264922706),
                        'scale': MinMaxScaler(),
                        },
                    'lasso': {
                        'features': ['50_g_HAspread_for_points-per-game', '50_g_HAspread_for_points-per-game`/`possessions-per-game', 'pregame_ppp_for', '20_game_avg_50_g_HAweight_for_points-per-game`/`possessions-per-game', 'expected_ppp_for', '25_g_HAspread_for_points-per-game`/`possessions-per-game', 'expected_pts_pg_for', 'pregame_pts_pg_for'],
                        'model': Lasso(random_state = 1108, alpha = 0.13526474650418807, max_iter = 2000),
                        'scale': StandardScaler(),
                        },
                    },
                'offensive_stats': {                       
                    'linsvm': {
                        'features': ['pregame_ftm-per-100-possessions_for', '100_g_HAspread_for_defensive-efficiency', '30_g_HAspread_for_floor-percentage', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_turnovers-per-possession_for', '100_g_HAspread_for_floor-percentage', '75_g_HAspread_for_floor-percentage', 'pregame_offensive-rebounding-pct_for', 'expected_offensive-rebounding-pct_for', 'pregame_effective-field-goal-pct_for', '100_g_HAspread_for_offensive-efficiency'],
                        'model': LinearSVR(random_state = 1108, C = 0.0869486130678, epsilon=0),
                        'scale': RobustScaler(),
                        },                          
                    'lightgbm': {
                        'features': ['pregame_ftm-per-100-possessions_for', '100_g_HAspread_for_defensive-efficiency', '30_g_HAspread_for_floor-percentage', 'expected_effective-field-goal-pct_for', 'expected_ftm-per-100-possessions_for', 'expected_turnovers-per-possession_for', '100_g_HAspread_for_floor-percentage', 'pregame_offensive-rebounding-pct_for', '75_g_HAspread_for_floor-percentage', 'expected_offensive-rebounding-pct_for', 'pregame_effective-field-goal-pct_for', '100_g_HAspread_for_offensive-efficiency'],
                        'model': lgb.LGBMRegressor(random_state = 1108, n_estimators = 500, colsample_bytree = 0.808603278021336, min_child_samples = 176, num_leaves = 24, subsample = 0.678375514083654, max_bin = 1032, learning_rate = 0.01),
                        'scale': MinMaxScaler()
                        }
                    }
                }
            }