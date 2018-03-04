import os
from gp import bayesian_optimisation
import numpy as np
from sklearn.model_selection import cross_val_score, KFold
from sklearn.gaussian_process.kernels import Matern
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
from sklearn.feature_selection import f_classif

try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
output_folder = os.path.join(cur_path, 'model_results')

def test_scaler(x, y):
    print('Searching for best scaler...')
    scores = []
    for scale in [StandardScaler(), MinMaxScaler(), RobustScaler()]:
        pipe = Pipeline([('scale',scale), ('clf',KNeighborsClassifier())])
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

def sample_loss_n_feats(parameters):
    feats = int(parameters[0])
    print('%s features' % (feats))
    model = Pipeline([('scale',scale),  ('clf',KNeighborsClassifier(leaf_size = leaf_, n_neighbors = n_))])
    score = cross_val_score(model, x_data[feat_sigs[:feats]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 1108))
    print('----> score: %s' % np.mean(score))
    return np.mean(score)

def find_feats():
    print('Searching for best number of features...')
    bounds = np.array([[1, len(list(x_data))]])
    start = [[len(list(x_data))]]
    results = bayesian_optimisation(n_iters=5,  
                          sample_loss=sample_loss_n_feats, 
                          bounds=bounds,
                          x0 = start,
                          gp_params = {'kernel': Matern(), 'alpha': 1e-5, 'n_restarts_optimizer': 10, 'normalize_y': True})
    return int(results[0][list(results[1]).index(max(results[1]))])

def sample_loss_leaf(parameters):
    leaf = int(parameters[0])
    n = int(parameters[1])
    model = Pipeline([('scale',scale), ('clf',KNeighborsClassifier(leaf_size = leaf, n_neighbors = n))])
    score = cross_val_score(model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 88))
    print('----> score: %s' % np.mean(score))
    return np.mean(score)
 
def leaf_tuning():
    print('-- Beginning leaf Search')
    bounds = np.array([[2, 100], [10, 200]])
    results = bayesian_optimisation(n_iters=12,  
                          sample_loss=sample_loss_leaf, 
                          bounds=bounds,
                          gp_params = {'kernel': Matern(), 'alpha': 1e-5, 'n_restarts_optimizer': 10, 'normalize_y': True})
    print('Best Neighbors: %s, Best Leafs: %s, Best score: %s' % (results[0][list(results[1]).index(max(results[1]))][0], results[0][list(results[1]).index(max(results[1]))][1], max(results[1]))) 
    return results[0][list(results[1]).index(max(results[1]))]

def execute(sa, od, X_data = None, Y_data = None):
#    sa, od, X_data, Y_data = y_val, x_vals, x_data, y_data
    x_data = X_data
    y_data = Y_data
    x_feats = list(x_data)
    global x_data
    global y_data
    
    scale = test_scaler(x_data, y_data) #minmax
    global scale
    f = open(os.path.join(output_folder, '%s-%s-knn.txt'%(sa, od)), 'w')
    f.write('scale: %s,'%(scale))
    f.close()
    

    leaf_ = 30
    n_ = 5
    global leaf_
    global n_
    
    feat_sigs = list(x_data)
    global feat_sigs
    features = len(feat_sigs)
    global features
    leaf_, n_ = leaf_tuning()
    leaf_, n_ = int(leaf_), int(n_) 
    global leaf_
    global n_
    f = open(os.path.join(output_folder,  '%s-%s-knn.txt'%(sa, od)), 'a')
    f.write('start neighbors: %s,'%(n_))
    f.write('start leaves: %s,'%(leaf_))
    f.close()

#    scale = MinMaxScaler()
#    leaf_, n_ = int(66), int(128) 
#    global scale
#    global leaf_
#    global n_    
    print('Starting feature ranking')
    sigs = f_classif(x_data, y_data)[1]
    indices = np.argsort(sigs)
    feat_sigs = [x_feats[i] for i in indices]
    global feat_sigs
    features = find_feats()
    global features
    f = open(os.path.join(output_folder,  '%s-%s-knn.txt'%(sa, od)), 'a')
    f.write('n feats: %s,'%(features))
    f.close()
    f = open(os.path.join(output_folder,  '%s-%s-knn.txt'%(sa, od)), 'a')
    f.write('significant features: ')
    for line in feat_sigs[:features]:
        f.write('%s, '%(line))
    f.close()
    
    leaf_, n_ = leaf_tuning()
    leaf_ = int(leaf_)
    n_ = int(n_)
    global leaf_
    global n_
    f = open(os.path.join(output_folder,  '%s-%s-knn.txt'%(sa, od)), 'a')
    f.write('final neighbors: %s,'%(n_))
    f.write('final leaves: %s,'%(leaf_))
    f.close()
    
    print('---Finalizing KNN Model')
    model = Pipeline([('scale',scale), ('clf',KNeighborsClassifier(leaf_size = leaf_, n_neighbors = n_))])                    
    tune_score = cross_val_score(model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 88))
    print('...KNN Model Finalized')
    tune_score = np.mean(tune_score)
    base_model = Pipeline([('scale',scale), ('clf',GaussianNB())])
    baseline_score = cross_val_score(base_model, x_data[feat_sigs], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
    baseline_score = np.mean(baseline_score)
    improvement = (tune_score - baseline_score)/baseline_score
    print('%s percent improvement from baseline' % (improvement * 100))
    if improvement < 0:
        f = open(os.path.join(output_folder, '%s-%s-knn.txt'%(sa, od)), 'a')
        f.write('final score: XXX,')
        f.close()
        return 0
    else:
        f = open(os.path.join(output_folder, '%s-%s-knn.txt'%(sa, od)), 'a')
        f.write('final score: %s,'%(tune_score))
        f.close()
        return tune_score
    