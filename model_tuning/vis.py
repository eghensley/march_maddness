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
sys.path.insert(-1, output_folder)
import pandas as pd
import matplotlib.pyplot as plt



for sort in ['ou', 'ml', 'line']:
    data = pd.read_csv(os.path.join(output_folder, '%s_bank.csv' % (sort)))
    x_label = []
    for each in list(data['idx']):
        x_label.append(each[:10])
    data['idx'] = x_label
    data = data.set_index('idx')
    pred_cols = list(data)
    for col_list in [pred_cols[i:][::11] for i in range(int((len(pred_cols)+1)/10))]:
        vis_data = data[col_list]
        plt.figure(figsize=(8,8))
        plt.plot(vis_data, linestyle = '-.')
        plt.title('%s by confidence'  % (sort))
        plt.ylabel('bank')
        plt.xlabel('date')
        plt.legend(col_list, loc='upper left')
        plt.show()
        
        
    for col_list in [pred_cols[i*11:11 + (i * 11)] for i in range(int((len(pred_cols)+1)/10)-1)]:
        vis_data = data[col_list]
        plt.figure(figsize=(8,8))
        plt.plot(vis_data, linestyle = '-.')
        plt.title('%s by model'  % (sort))
        plt.ylabel('bank')
        plt.xlabel('date')
        plt.legend(col_list, loc='upper left')
        plt.show()
        
    
    all_finals = []
    for each in pred_cols:
        all_finals.append(int(data[each][len(data)-1:].values))
        
    top_finals = sorted(all_finals, reverse = True)[:10]
    top_results = [all_finals.index(i) for i in top_finals]
    top_list = [pred_cols[i] for i in top_results]

    vis_data = data[top_list]
    plt.figure(figsize=(8,8))
    plt.plot(vis_data, linestyle = '-.')
    plt.title('top %s'  % (sort))
    plt.ylabel('bank')
    plt.xlabel('date')
    plt.legend(top_list, loc='upper left')
    plt.show()