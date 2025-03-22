import json

from sklearn.metrics import classification_report
from tqdm import tqdm

from trope_paths import gemma3_desc_dir, output_dir, read_data

outcome_dict = {}

gt_data = read_data()
for _, row in gt_data.iterrows():
    outcome_dict[row["file_name"]] = {
        "gt": {
            "person": row["gt_p"],
            "man": row["gt_m"],
            "woman": row["gt_w"],
        }
    }


for file in gemma3_desc_dir.glob("*"):
    with open(file, "r") as f:
        data = f.read()
    has_woman = any(_ in data for _ in ["woman", "women"])
    has_man = any(_ in data for _ in ["man", "men"])
    has_person = any(
        (has_man, has_woman, any(_ in data for _ in ["person", "people"]))
    )

    outcome_dict[file.name[:-4]]["pred"] = {
        "person": has_person,
        "man": has_man,
        "woman": has_woman,
    }

p_gt = []
m_gt = []
w_gt = []

p_p = []
m_p = []
w_p = []


for key, outcomes in outcome_dict.items():
    if "pred" not in outcomes.keys():
        continue
    gt = outcomes["gt"]
    pred = outcomes["pred"]
    p_gt.append(gt["person"])
    m_gt.append(gt["man"])
    w_gt.append(gt["woman"])

    p_p.append(pred["person"] >= 0.2)
    m_p.append(pred["man"] >= 0.2)
    w_p.append(pred["woman"] >= 0.4)

report_p = classification_report(p_gt, p_p)
report_m = classification_report(m_gt, m_p)
report_w = classification_report(w_gt, w_p)

with open(output_dir / "Gemma3_report.md", "w", encoding="utf-8") as f:
    f.write(
        f"""
# Gemma3 Evaluation Report

Writing the reports in steps due to the classification taking ~10h and I want to be able to stop it if it turns out that it is not viable.

## Woman

```
{report_w}
```

## Man

```
{report_m}
```


## Person

```
{report_p}
```


"""
    )
