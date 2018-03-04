import sklearn_vegas_preds
import keras_vegas_preds
import voter_vegas_preds

def predict():
    sklearn_vegas_preds.sklearn_preds()
    keras_vegas_preds.keras_preds()
    voter_vegas_preds.voter()
    
if __name__ == '__main__':
    predict()