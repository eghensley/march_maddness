import os
from gp import bayesian_optimisation
import numpy as np
from sklearn.model_selection import cross_val_score, KFold
from sklearn.gaussian_process.kernels import Matern
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import pandas as pd
from sklearn.feature_selection import f_regression
from sklearn.naive_bayes import GaussianNB

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
        pipe = Pipeline([('scale',scale), ('clf',LogisticRegression(random_state = 1108))])
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
    model = Pipeline([('scale',scale),  ('clf',LogisticRegression(random_state = 1108, solver = solver_, C = C_))])
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

def test_solver(x, y):
    print('Searching for best solver...')
    scores = []
    for slvr in ['liblinear', 'newton-cg', 'lbfgs', 'sag','saga']:
        pipe = Pipeline([('scale',scale), ('clf',LogisticRegression(random_state = 1108, solver = slvr, C = C_))])
        score = cross_val_score(pipe, x, y, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
        scores.append(np.mean(score))
    if scores.index(max(scores)) == 0:
        print('Using liblinear')
        return 'liblinear'
    elif scores.index(max(scores)) == 1:
        print('Using newton-cg')
        return 'newton-cg'
    elif scores.index(max(scores)) == 2:
        print('Using lbfgs')
        return 'lbfgs'
    elif scores.index(max(scores)) == 3:
        print('Using sag')
        return 'sag'
    elif scores.index(max(scores)) == 4:
        print('Using saga')
        return 'saga'
    
def sample_loss_c(parameters):
    c = 10**parameters[0]
    model = Pipeline([('scale',scale), ('clf',LogisticRegression(random_state = 1108, C = c))])
    score = cross_val_score(model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 88))
    print('----> score: %s' % np.mean(score))
    return np.mean(score)
 
def c_tuning():
    print('-- Beginning C Search')
    bounds = np.array([[-3, 3]])
    results = bayesian_optimisation(n_iters=5,  
                          sample_loss=sample_loss_c, 
                          bounds=bounds,
                          gp_params = {'kernel': Matern(), 'alpha': 1e-5, 'n_restarts_optimizer': 10, 'normalize_y': True})
    print('Best C: %s, Best score: %s' % (results[0][list(results[1]).index(max(results[1]))][0], max(results[1]))) 
    return 10**results[0][list(results[1]).index(max(results[1]))][0]

def execute(sa, od, X_data = None, Y_data = None):
    x_data = X_data
    y_data = Y_data
    x_feats = list(x_data)
    global x_data
    global y_data
    
    scale = test_scaler(x_data, y_data) #minmax
    global scale
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'w')
    f.write('scale: %s,'%(scale))
    f.close()
    
    C_ = 1
    global C_
    solver_ = test_solver(x_data, y_data)
    global solver_
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('start solver: %s,'%(solver_))
    f.close()

    feat_sigs = list(x_data)
    global feat_sigs
    features = len(feat_sigs)
    global features
    C_ = c_tuning()
    global C_
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('start C: %s,'%(C_))
    f.close()

    print('Starting feature ranking')
    sigs = f_regression(x_data, y_data)[1]
    indices = np.argsort(sigs)
    feat_sigs = [x_feats[i] for i in indices]
    global feat_sigs
    features = find_feats()
    global features
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('n feats: %s,'%(features))
    f.close()
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('significant features: ')
    for line in feat_sigs[:features]:
        f.write('%s, '%(line))
    f.close()
    
    solver_ = test_solver(x_data[feat_sigs[:features]], y_data)
    global solver_
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('final solver: %s,'%(solver_))
    f.close()

    C_ = c_tuning()
    f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
    f.write('final C: %s,'%(C_))
    f.close()
    
    print('---Finalizing Log Model')
    model = Pipeline([('scale',scale), ('clf',LogisticRegression(random_state = 1108, solver = solver_, C = C_))])                    
    tune_score = cross_val_score(model, x_data[feat_sigs[:features]], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 88))
    print('...Log Model Finalized')
    tune_score = np.mean(tune_score)
    base_model = Pipeline([('scale',scale), ('clf',GaussianNB())])
    baseline_score = cross_val_score(base_model, x_data[feat_sigs], y_data, scoring = 'accuracy' ,cv = KFold(n_splits = 10, random_state = 86))
    baseline_score = np.mean(baseline_score)
    improvement = (tune_score - baseline_score)/baseline_score
    print('%s percent improvement from baseline' % (improvement * 100))
    if improvement < 0:
        f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
        f.write('final score: XXX,')
        f.close()
        return 0
    else:
        f = open(os.path.join(output_folder, '%s-%s-log.txt'%(sa, od)), 'a')
        f.write('final score: %s,'%(tune_score))
        f.close()
        return tune_score
    