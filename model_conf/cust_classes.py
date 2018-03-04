import pandas as pd

class VotingClassifier():
    def __init__(self):
        self._stored_models = {}

    def load(self, model, weight, data):
        i = 0
        while i in self._stored_models.keys():
            i += 1
            
        preds = model.predict_proba(data)
        model_df = pd.DataFrame()
        model_df['idx'] = list(data.index)
        pred_zero = []
        pred_one = []
        for each in preds:
            pred_zero.append(each[0] * weight)
            pred_one.append(each[1] * weight)

        model_df['zero_'+str(i)] = pred_zero
        model_df['one_'+str(i)] = pred_one
        model_df = model_df.set_index('idx')
        self._stored_models[i] = model_df
        

#    def process(self):
        
       

       
        
        
#    def predict_proba(self, x):   
#        all_preds = []
#        for i in range(len(x)):
#            ind_x = x.iloc[i]
#            ind_1 = []
#            ind_2 = []
#            for each in self._stored_models.values():
#                pred = each['model'].predict_proba(ind_x[each['features']].values.reshape(1,-1))     
#                ind_1.append(pred[0][0] * each['weight'])
#                ind_2.append(pred[0][1] * each['weight'])
#            all_preds.append([ind_1, ind_2])        
#        return all_preds
#  
#    def predict(self, x):   
#        all_preds = []
#        for i in range(len(x)):
#            ind_x = x.iloc[i]
#            ind_1 = []
#            ind_2 = []
#            for each in self._stored_models.values():
#                pred = each['model'].predict_proba(ind_x[each['features']].values.reshape(1,-1))     
#                ind_1.append(pred[0][0] * each['weight'])
#                ind_2.append(pred[0][1] * each['weight'])
#            if ind_1 > ind_2:
#                all_preds.append(0)        
#            else:
#                all_preds.append(1)
#        return all_preds