import pickle_classifiers
import pickle_derived_predictors
import pickle_keras_classifier
import pickle_ranking_predictors
import pickle_vegas_predictors

if __name__ == '__main__':
    pickle_classifiers.save()
    pickle_derived_predictors.save()
    pickle_keras_classifier.save()
    pickle_ranking_predictors.save()
    pickle_vegas_predictors.save()