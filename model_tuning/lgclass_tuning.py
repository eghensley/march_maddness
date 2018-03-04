import os, sys

try:
    import lightgbm as lgb
except ImportError:
    sys.path.insert(-1, "/home/eric/LightGBM/python-package")
    import lightgbm as lgb
from gp import bayesian_optimisation
import numpy as np
from sklearn.model_selection import cross_val_score, KFold
from sklearn.gaussian_process.kernels import RBF, RationalQuadratic, Matern
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
import pandas as pd

try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
output_folder = os.path.join(cur_path, 'model_results')

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

def test_scaler(x, y):
    print('Searching for best scaler')
    scores = []
    for scale in [StandardScaler(), MinMaxScaler(), RobustScaler()]:
        pipe = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108))])
        score = cross_val_score(pipe, x, y, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 46))
        scores.append(np.mean(score))
    if scores.index(max(scores)) == 0:
        print('Using Standard Scaler')
        return StandardScaler()
    elif scores.index(max(scores)) == 1:
        print('Using Min Max Scaler')
        return MinMaxScaler()
    elif scores.index(max(scores)) == 2:
        print('Using Robust Scaler')
        return RobustScaler()

def check_lr(lr, x, y, scale):
    scores = []
    for tree in [75, 100, 125]:
        test = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = tree, subsample = .8, learning_rate = lr))])
        score = cross_val_score(test, x, y, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
        scores.append(np.mean(score))
    return scores.index(max(scores))

def find_lr(start_lr, x_, y, scale):
    print('Searching for best learning rate')
    last = None
    while start_lr:
        x = check_lr(start_lr, x_, y, scale)
        if x == 0:
            if last == 2:
                learn_rate = np.mean([start_lr, start_lr /2])
                print('Learning Rate: %s' % (learn_rate))
                start_lr = False
            else:
                start_lr /= 2
        elif x==1:
            learn_rate = start_lr
            print('Learning Rate: %s' % (learn_rate))
            print('---- Best Learning Rate')
            start_lr = False
        elif x==2:
            if last == 0:
                learn_rate = np.mean([start_lr, start_lr/2])
                print('Learning Rate: %s' % (learn_rate))
                start_lr = False
            else:
                start_lr *= 2
        last = x
    return learn_rate

def sample_loss_n_feats(parameters):
    feats = int(parameters[0])
    if feats == 0:
        feats = 1
    print('%s features' % (feats))
    model = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, subsample = .8, learning_rate = learn_rate))])
    score = cross_val_score(model, x_data[feat_sigs[:feats]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 1108))
    print('----> score: %s' % np.mean(score))
    return np.mean(score)

def find_feats():
    print('Searching for best number of features')
    bounds = np.array([[1, len(list(x_data))]])
    start = [[len(list(x_data))]]
    results = bayesian_optimisation(n_iters=8,  
                          sample_loss=sample_loss_n_feats, 
                          bounds=bounds,
                          x0 = start,
                          gp_params = {'kernel': Matern(), 'alpha': 1e-5, 'n_restarts_optimizer': 10, 'normalize_y': True})
    return int(results[0][list(results[1]).index(max(results[1]))])

def sample_loss_hyperparameters(parameters):
    tree_sample = parameters[0]
    bin_max = int(parameters[1])
    child_samples = int(parameters[2])
    leaves = int(parameters[3])
    sample = parameters[4]
    model = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, colsample_bytree = tree_sample, min_child_samples = child_samples, num_leaves = leaves, subsample = sample, max_bin = bin_max, learning_rate = new_learn_rate))])
    score = cross_val_score(model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 88))
    print('----> score: %s' % np.mean(score))
    return np.mean(score)
 
def hyper_parameter_tuning():
    print('Searching hyper parameters')
    result_list = []
    params_list = []
    for ker in [RBF(), RationalQuadratic(), Matern()]: #ExpSineSquared(), 
        print('-- Beginning Gaussian Search with %s' % (ker))
        bounds = np.array([[.6, 1], [1000, 2000], [1, 200], [10, 200], [.4, 1]])
        results = bayesian_optimisation(n_iters=15,  
                              sample_loss=sample_loss_hyperparameters, 
                              bounds=bounds,
                              gp_params = {'kernel': ker, 'alpha': 1e-5, 'n_restarts_optimizer': 10, 'normalize_y': True})
        print('Kernel: %s, Best score: %s' % (ker, max(results[1]))) 
        result_list.append(results[1])
        params_list.append(results[0])
    return result_list, params_list

def drop_lr(l_drop, trees):
    prev_score = 0
    prev_trees = 0
    for trial in np.linspace(1.5, 8.5, 15):
        num_trees = trees * trial
        model_lr = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = int(num_trees), colsample_bytree = colsample, min_child_samples = int(min_child), num_leaves = int(n_leaves), subsample = sub_sample, max_bin = int(bin_size), learning_rate = l_drop))])
        lr_score = cross_val_score(model_lr, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 151))
        if np.mean(lr_score) > prev_score:
            print('%s x trees IMPROVEMENT, continuing'  % (trial))
            prev_score = np.mean(lr_score)
            prev_trees = num_trees
        else:
            print('%s x trees NO IMPROVEMENT'  % (trial))
            return prev_score, prev_trees

def execute(sa, od, X_data = None, Y_data = None):
    x_data = X_data
    x_feats = list(x_data)
    y_data = Y_data
    global x_data
    global y_data
    
    scale = test_scaler(x_data, y_data) #minmax
    global scale
    f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'w')
    f.write('scale: %s,'%(scale))
    f.close()
    
    learn_rate = find_lr(.01, x_data, y_data, scale)
    global learn_rate
    f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
    f.write('start lr: %s,'%(learn_rate))
    f.close()
    
    model = lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, subsample = .8, learning_rate = learn_rate)
    model.fit(scale.fit_transform(x_data), y_data)
    sigs = model.feature_importances_
    indices = np.argsort(sigs)[::-1]
    feat_sigs = [x_feats[i-1] for i in indices]
    global feat_sigs
    features = find_feats()
    global features
    f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
    f.write('start n feats: %s,'%(features))
    f.close()
    
    new_learn_rate = find_lr(learn_rate, x_data[feat_sigs[:features]], y_data, scale)
    global new_learn_rate
    f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
    f.write('significant features: ')
    for line in feat_sigs[:features]:
        f.write('%s, '%(line))
    f.close()
    results, params = hyper_parameter_tuning()
    gauss_results = pd.DataFrame()
    for result_batch, param_batch in zip(results, params):
        for result_item, param_item in zip(result_batch, param_batch):
            gauss_results = gauss_results.append({'score':result_item, 'colsample_bytree':param_item[0], 'max_bin': int(param_item[1]), 'min_child_samples': int(param_item[2]), 'num_leaves' : int(param_item[3]), 'subsample': param_item[4]}, ignore_index = True)
    gauss_results.to_csv(os.path.join(output_folder, '%s-%s-lightc-results.csv'%(sa, od)))
    
    base_model = Pipeline([('scale',scale), ('clf',GaussianNB())])
    baseline_score = cross_val_score(base_model, x_data[feat_sigs], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
    baseline_score = np.mean(baseline_score)
    colsample, bin_size, min_child, n_leaves, score_val, sub_sample = gauss_results.sort_values('score', ascending = False)[:1].values[0]
    global colsample
    global bin_size
    global min_child
    global n_leaves
    global sub_sample
    
    tune_model = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = 100, colsample_bytree = colsample, min_child_samples = int(min_child), num_leaves = int(n_leaves), subsample = sub_sample, max_bin = int(bin_size), learning_rate = new_learn_rate))])    
    tune_score = cross_val_score(tune_model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
    tune_score = np.mean(tune_score)        
        
    lr_drop = new_learn_rate
    trees_drop = 100
    
    dropped_score_val = score_val
    improvement = 0
    if type(baseline_score) is np.float64:
        improvement = (tune_score - baseline_score)/baseline_score
        print('%s percent improvement from baseline, dropping learning rate' % (improvement * 100))
    
    while improvement >= 0 and trees_drop <= 5000:
        drop_scores, drop_trees = drop_lr(lr_drop/2, trees_drop)
        print('Previous best score of: %s' % (dropped_score_val))
        print('Max test score of: %s' % (drop_scores)) 
        print('Best test trees: %s' % (drop_trees))
        improvement = drop_scores - dropped_score_val
        if improvement >= 0:
            lr_drop /= 2
            trees_drop = drop_trees
            print('Continuing Search')
            print('Trees: %s'%(trees_drop))
            dropped_score_val = drop_scores
        else:
            print('Optimized Trees/LR Found')
            print('---- Trees: %s'%(trees_drop))
            print('---- LR: %s'%(lr_drop))
            
    f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
    f.write('trees: %s,' % (trees_drop))
    f.write('lr: %s,'%(lr_drop))
    f.close()
        
    print('--- Finalizing Light GBC model')    
    model_lr = Pipeline([('scale',scale), ('clf',lgb.LGBMClassifier(random_state = 1108, n_estimators = int(trees_drop), colsample_bytree = colsample, min_child_samples = int(min_child), num_leaves = int(n_leaves), subsample = sub_sample, max_bin = int(bin_size), learning_rate = lr_drop))])
    tune_score = cross_val_score(model_lr, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 151))
    print('...Light GBC finalized')
    tune_score = np.mean(tune_score)
    improvement = (tune_score - baseline_score)/baseline_score
    if improvement < 0:
        f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
        f.write('final score: XXX,')
        f.close()
        return 0
    else:
        f = open(os.path.join(output_folder, '%s-%s-lightc.txt'%(sa, od)), 'a')
        f.write('final score: %s,'%(tune_score))
        f.close()
        return tune_score