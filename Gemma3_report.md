
# Gemma3 Evaluation Report

Writing the reports in steps due to the classification taking ~10h and I want to be able to stop it if it turns out that it is not viable.

## Woman

```
              precision    recall  f1-score   support

       False       0.93      0.76      0.84        50
        True       0.80      0.94      0.86        50

    accuracy                           0.85       100
   macro avg       0.86      0.85      0.85       100
weighted avg       0.86      0.85      0.85       100

```

## Man

```
              precision    recall  f1-score   support

       False       0.96      0.38      0.55        60
        True       0.51      0.97      0.67        40

    accuracy                           0.62       100
   macro avg       0.74      0.68      0.61       100
weighted avg       0.78      0.62      0.60       100

```


## Person

```
              precision    recall  f1-score   support

       False       0.00      0.00      0.00        32
        True       0.68      1.00      0.81        68

    accuracy                           0.68       100
   macro avg       0.34      0.50      0.40       100
weighted avg       0.46      0.68      0.55       100

```
