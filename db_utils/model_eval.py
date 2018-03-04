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

import pandas as pd
import pull_data
import update_dbs
import numpy as np

vegas_data = pull_data.pull_odds_data(update_dbs.mysql_client())
#stored_results = {}
#for sort in ['ou', 'winner', 'line']:

#def moneyline_analysis():
#    ml_data = vegas_data[['fav-ml', 'dog-ml', 'fav_idx', 'dog_idx', 'fav-score', 'dog-score']]
#    ml_data = ml_data.dropna(how = 'any')
#    vegas_target_1 = 'fav-ml'
#    vegas_target_2 = 'dog-ml'
#    
#    
#    print('------ vegas: money-line')
#    data = pd.read_csv(os.path.join(output_folder, 'winner_results.csv'))
#    data = data.set_index('idx')
#    
#    pred_cols = list(data)
#    odds_index = list(ml_data.set_index('fav_idx').join(data, how = 'inner').index)
#    vegas = {}
#    vegas['idx'] = odds_index
#    for prediction, confidence in zip(pred_cols[::2], pred_cols[1:][::2]):
#        print('--- model: %s' % (prediction))
#        for threshold in [0,.01,.02,.03,.04,.05,.05,.06,.07,.08,.09,.1]:
#            print('-- threshold: %s' % (threshold))
#            bank = 1000
#            record = []
#            for i in odds_index:
#                
#                dif = float(ml_data.loc[vegas_data['fav_idx'] == i][['dog-score']].values) - float(ml_data.loc[vegas_data['fav_idx'] == i][['fav-score']].values)
#                
#                if dif < 0:
#                    actual = 1
#                else:
#                    actual = 0
#                    
#                tm1_idx = str(ml_data.loc[vegas_data['fav_idx'] == i][['fav_idx']].values[0][0])
#                tm2_idx = str(ml_data.loc[vegas_data['fav_idx'] == i][['dog_idx']].values[0][0])
#                
#                team1_pred = int(data[[prediction]].loc[tm1_idx].values)
#                team1_conf = float(data[[confidence]].loc[tm1_idx].values)
#
##                team2_pred = int(data[[prediction]].loc[tm2_idx].values)
##                team2_conf = float(data[[confidence]].loc[tm2_idx].values)            
#            
##                if team2_pred != team1_pred:
##                    pred = team1_pred
##                    conf = np.mean([team1_conf, team2_conf])
##                else:
##                    if team1_conf > team2_conf:
##                        conf = .5 + (team1_conf - team2_conf)
##                        pred = team1_pred
##                    else:
##                        conf = .5 + (team2_conf - team1_conf)
##                        pred = team2_pred
#                pred = team1_pred
#                conf = team1_conf
#
#                ml_fav = float(ml_data[ml_data['fav_idx'] == i][[vegas_target_1]].values)
#                ml_dog = float(ml_data[ml_data['fav_idx'] == i][[vegas_target_2]].values)
#                
#                if pred == 1:
#                    break_even = (-(ml_fav) / ((-(ml_fav))+100))
#                    risk = abs(ml_fav)
#                    payout = 100
#                else:
#                    break_even = 100 / (ml_dog + 100)
#                    risk = 100
#                    payout = ml_dog
#                    
#                make_bet = False
#                
#                if conf > break_even + threshold:
#                    make_bet = True
#                                                  
#                if make_bet:
#                    if pred == actual:
#                        bank += payout
#                    else:
#                        bank -= risk
#                
#                record.append(bank)
#                
#            vegas['%s_%s' % (prediction, threshold)] = record
#            
#    bank_results = pd.DataFrame.from_dict(vegas)
#    bank_results = bank_results.set_index('idx')
#    bank_results.to_csv(os.path.join(output_folder, 'ml_bank.csv'))  

def line_analysis():
    ou_data = vegas_data[['line', 'line-juice', 'fav_idx', 'dog_idx', 'fav-score', 'dog-score']]
    ou_data = ou_data.dropna(how = 'any')
    vegas_target_1 = 'line'
    vegas_target_2 = 'line-juice'
    
    
    print('------ vegas: line')
    data = pd.read_csv(os.path.join(output_folder, 'line_results.csv'))
    data = data.set_index('idx')
    
    pred_cols = list(data)
    odds_index = list(ou_data.set_index('fav_idx').join(data, how = 'inner').index)
    vegas = {}
    vegas['idx'] = odds_index
    for prediction, confidence in zip(pred_cols[::2], pred_cols[1:][::2]):
        print('--- model: %s' % (prediction))
        for threshold in [0,.01,.02,.03,.04,.05,.05,.06,.07,.08,.09,.1]:
            print('-- threshold: %s' % (threshold))
            bank = 1000
            record = []
            for i in odds_index:
                
                target = float(ou_data[ou_data['fav_idx'] == i][[vegas_target_1]].values)
                juice = float(ou_data[ou_data['fav_idx'] == i][[vegas_target_2]].values)
                
                fav_juice = False

                if juice == 0:
                    juice = 10.0
                elif juice < 0:
                    juice = abs(juice)
                    fav_juice = True

                dif = float(ou_data.loc[vegas_data['fav_idx'] == i][['dog-score']].values) - float(ou_data.loc[vegas_data['fav_idx'] == i][['fav-score']].values)
                
                if dif < target:
                    actual = 1
                else:
                    actual = 0
                    
                tm1_idx = str(ou_data.loc[vegas_data['fav_idx'] == i][['fav_idx']].values[0][0])
                tm2_idx = str(ou_data.loc[vegas_data['fav_idx'] == i][['dog_idx']].values[0][0])
                
                team1_pred = int(data[[prediction]].loc[tm1_idx].values)
                team1_conf = float(data[[confidence]].loc[tm1_idx].values)

                team2_pred = int(data[[prediction]].loc[tm2_idx].values)
                team2_conf = float(data[[confidence]].loc[tm2_idx].values)            
            
                if team2_pred != team1_pred:
                    pred = team1_pred
                    conf = np.mean([team1_conf, team2_conf])
                else:
                    if team1_conf > team2_conf:
                        conf = .5 + (team1_conf - team2_conf)
                        pred = team1_pred
                    else:
                        conf = .5 + (team2_conf - team1_conf)
                        pred = abs(1 - team2_pred)
                    
                
                make_bet = False
                
                if pred == 0:
                    if fav_juice:
                        risk = 110 - (juice - 10)
                    else:
                        risk = 110 + (juice - 10)
                else:
                    if fav_juice:
                        risk = 110 + (juice - 10)
                    else:
                        risk = 110 - (juice - 10)
                        
                break_even = risk/(100 + risk)
                
                if conf > break_even + threshold:
                    make_bet = True
                    
                if make_bet:
                    if pred == actual:
                        bank += 100
                    else:
                        bank -= risk
                
                record.append(bank)
                
            vegas['%s_%s' % (prediction, threshold)] = record
            
    bank_results = pd.DataFrame.from_dict(vegas)
    bank_results = bank_results.set_index('idx')
    bank_results.to_csv(os.path.join(output_folder, 'line_bank.csv'))   

def over_under_analysis():
    ou_data = vegas_data[['overunder', 'ou-juice', 'fav_idx', 'dog_idx', 'fav-score', 'dog-score']]
    ou_data = ou_data.dropna(how = 'any')
    vegas_target_1 = 'overunder'
    vegas_target_2 = 'ou-juice'
    
    
    print('------ vegas: over under')
    data = pd.read_csv(os.path.join(output_folder, 'ou_results.csv'))
    data = data.set_index('idx')
    
    pred_cols = list(data)
    odds_index = list(ou_data.set_index('fav_idx').join(data, how = 'inner').index)
    vegas = {}
    vegas['idx'] = odds_index
    for prediction, confidence in zip(pred_cols[::2], pred_cols[1:][::2]):
        print('--- model: %s' % (prediction))
        for threshold in [0,.01,.02,.03,.04,.05,.05,.06,.07,.08,.09,.1]:
            print('-- threshold: %s' % (threshold))
            bank = 1000
            record = []
            for i in odds_index:
                target = float(ou_data[ou_data['fav_idx'] == i][[vegas_target_1]].values)
                juice = float(ou_data[ou_data['fav_idx'] == i][[vegas_target_2]].values)
                
                over_juice = False

                if juice == 0:
                    juice = 10.0
                elif juice < 0:
                    juice = abs(juice)
                    over_juice = True

                total = float(ou_data.loc[vegas_data['fav_idx'] == i][['fav-score']].values) + float(ou_data.loc[vegas_data['fav_idx'] == i][['dog-score']].values)
                
                if total > target:
                    actual = 1
                else:
                    actual = 0
                    
                tm1_idx = str(ou_data.loc[vegas_data['fav_idx'] == i][['fav_idx']].values[0][0])
                tm2_idx = str(ou_data.loc[vegas_data['fav_idx'] == i][['dog_idx']].values[0][0])
                
                team1_pred = int(data[[prediction]].loc[tm1_idx].values)
                team1_conf = float(data[[confidence]].loc[tm1_idx].values)

                team2_pred = int(data[[prediction]].loc[tm2_idx].values)
                team2_conf = float(data[[confidence]].loc[tm2_idx].values)            
            
                if team2_pred == team1_pred:
                    pred = team1_pred
                    conf = np.mean([team1_conf, team2_conf])
                else:
                    if team1_pred == 0:
                        team1_conf = 1 - team1_conf
                    else:
                        team2_conf = 1 - team2_conf
                    
                    conf = np.mean([team1_conf, team2_conf])
                    if conf < .5:
                        pred = 0
                    else:
                        pred = 1
                
                make_bet = False
                
                if pred == 0:
                    if over_juice:
                        risk = 110 - (juice - 10)
                    else:
                        risk = 110 + (juice - 10)
                else:
                    if over_juice:
                        risk = 110 + (juice - 10)
                    else:
                        risk = 110 - (juice - 10)
                        
                break_even = risk/(100 + risk)
                
                if conf > break_even + threshold:
                    make_bet = True
                    
                if make_bet:
                    if pred == actual:
                        bank += 100
                    else:
                        bank -= risk
                
                record.append(bank)
                
            vegas['%s_%s' % (prediction, threshold)] = record
            
    bank_results = pd.DataFrame.from_dict(vegas)
    bank_results = bank_results.set_index('idx')
    bank_results.to_csv(os.path.join(output_folder, 'ou_bank.csv'))


if __name__ == '__main__':
    line_analysis()
    over_under_analysis()
#    moneyline_analysis()
