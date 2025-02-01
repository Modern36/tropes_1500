# Ollama Evaluation Report

            Writing the reports in steps due to the classification taking ~10h and I want to be able to stop it if it turns out that it is not viable.

        ## Woman

                      precision    recall  f1-score   support

       False       0.82      0.90      0.86        10
        True       0.89      0.80      0.84        10

    accuracy                           0.85        20
   macro avg       0.85      0.85      0.85        20
weighted avg       0.85      0.85      0.85        20


           ## Man

                         precision    recall  f1-score   support

       False       1.00      0.54      0.70        13
        True       0.54      1.00      0.70         7

    accuracy                           0.70        20
   macro avg       0.77      0.77      0.70        20
weighted avg       0.84      0.70      0.70        20


            ## Person

                          precision    recall  f1-score   support

       False       0.00      0.00      0.00         6
        True       0.65      0.79      0.71        14

    accuracy                           0.55        20
   macro avg       0.32      0.39      0.35        20
weighted avg       0.45      0.55      0.50        20
