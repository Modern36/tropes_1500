# Statistics

The statistics are calculated as a classification problem: either the model
detects a (wo)man in the image or not. These predictions are then compared
to the *ground truth* labels from the manual annotation.

Since finding men or women in the image are two different problems, the
statistics are computed separately for each case. The performance statistics
are calculated using the scikit-learn
[`classification_report`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html#sklearn.metrics.classification_report)
function. **Scikit-learn ** is a renown python-library for Machine Learning.

The report contains several different metrics that together form a picture
of how well the model is performing and an insight into why it fails to
do a perfect job.

- **Precision**: The precision is the ratio of correctly predicted positive
cases to all predicted positive cases. High precision means that a positive
prediction is actually positive -- we we can trust that an image contains a
(wo)man when the model says so.

- **Recall**: The recall is the ratio of correctly predicted positive cases to
all actual positive cases. high recall means that a negative prediction is
actually negative -- we can trust that an image does NOT contains a (wo)man
when the model says it does NOT contain a (wo)man.

- **F1 score**: The F1 score is the
[harmonic mean](https://en.wikipedia.org/wiki/Harmonic_mean) of Precision and
Recall.

- **Support**: The support is the number of occurrences of each class (True --
 contains a (wo)man or False -- does not contain a (wo)man).

- **Accuracy**: The accuracy is the ratio of *correctly* (True or False)
predicted cases to all cases.

- **Macro average**: Arithmetic mean of the metric.

- **Weighted avg**: Weighted mean of the metric -- takes the size of each class
(support) into account.

## Files and directories

The statistics have been calculated twice:
once for the [20 selected images](/statistics/20_picked/) and another time
for the full set of [1500 annotated images](/statistics/overall).

Each directory contains four files:

1. `dmw.md` -- DinoManWoman (Grounding Dino with "man" entered before "Woman").
2. `dwm.md` -- DinoWoman (Grounding Dino with "Woman" entered before "man")/
3. `vqa.md` -- For the ViLT-VQA model.
4. `yolo.md` -- Limited to finding people (ignores gender).
