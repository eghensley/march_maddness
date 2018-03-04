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
model_storage = os.path.join(cur_path, 'saved_models')

import numpy as np
import pandas as pd
import saved_models

def voter():
    for sort in ['ou', 'winner', 'line']:
        data = pd.read_csv(os.path.join(output_folder, '%s_results.csv' % (sort)))
        data = data.set_index('idx')
         
        acc_vote_pred = []
        loss_vote_pred = []
        comb_vote_pred = []
        
        acc_vote_conf = []
        loss_vote_conf = []
        comb_vote_conf = []
        for i in list(data.index):
            acc_vote_zero = []
            acc_vote_one = []
    
            loss_vote_zero = []
            loss_vote_one = []
            
            comb_vote_zero = []
            comb_vote_one = []
            
            game = data.loc[i]
            
            for kind in ['+pts', 'raw']:
                for model_name, model_details in saved_models.stored_models[sort][kind].items():            
                    if int(game['%s_%s_prediction' % (kind, model_name)]) == 1:
                        zero = 1 - game['%s_%s_confidence' % (kind, model_name)]
                        one = game['%s_%s_confidence' % (kind, model_name)]                    
                        
                        acc_vote_zero.append(zero * model_details['acc_weight'])
                        acc_vote_one.append(one * model_details['acc_weight'])
    
                        loss_vote_zero.append(zero * model_details['logloss_weight'])
                        loss_vote_one.append(one * model_details['logloss_weight'])
    
                        comb_vote_zero.append(zero * model_details['combined_weight'])
                        comb_vote_one.append(one * model_details['combined_weight'])
    
                    else:
                        zero = game['%s_%s_confidence' % (kind, model_name)]
                        one = 1 - game['%s_%s_confidence' % (kind, model_name)]
                        
                        acc_vote_zero.append(zero * model_details['acc_weight'])
                        acc_vote_one.append(one * model_details['acc_weight'])
    
                        loss_vote_zero.append(zero * model_details['logloss_weight'])
                        loss_vote_one.append(one * model_details['logloss_weight'])
    
                        comb_vote_zero.append(zero * model_details['combined_weight'])
                        comb_vote_one.append(one * model_details['combined_weight'])
                        
    
    
    
                
            
            acc_zero = np.sum(acc_vote_zero)
            acc_one = np.sum(acc_vote_one)
            loss_zero = np.sum(loss_vote_zero)
            loss_one = np.sum(loss_vote_one)        
            comb_zero = np.sum(comb_vote_zero)
            comb_one = np.sum(comb_vote_one)        
            
            if acc_zero > acc_one:
                acc_vote_pred.append(0)
                acc_vote_conf.append(acc_zero)
            else:
                acc_vote_pred.append(1)
                acc_vote_conf.append(acc_one)
    
    
            if loss_zero > loss_one:
                loss_vote_pred.append(0)
                loss_vote_conf.append(loss_zero)
            else:
                loss_vote_pred.append(1)
                loss_vote_conf.append(loss_one)
    
    
            if comb_zero > comb_one:
                comb_vote_pred.append(0)
                comb_vote_conf.append(comb_zero)
            else:
                comb_vote_pred.append(1)
                comb_vote_conf.append(comb_one)
                
            
        data['accuracy_voter_prediction'] = acc_vote_pred
        data['accuracy_voter_confidence'] = acc_vote_conf
        
        data['loss_voter_prediction'] = loss_vote_pred
        data['loss_voter_confidence'] = loss_vote_conf
            
                        
        data['combined_voter_prediction'] = comb_vote_pred
        data['combined_voter_confidence'] = comb_vote_conf           
                
                
        data.to_csv(os.path.join(output_folder, '%s_results.csv' % (sort)))