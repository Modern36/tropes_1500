from trope_paths import read_data, output_dir, moon_tmp_qa
from tqdm import tqdm
import json
from sklearn.metrics import classification_report

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


for file in moon_tmp_qa.glob("*"):
    with open(file, "r") as f:
        data = f.read()
    data_dict = json.loads(data)
    pred_people = data_dict["people"]
    pred_men = data_dict["man"]
    pred_women = data_dict["woman"]
    outcome_dict[file.name[:-5]]["pred"] = {
        "person": pred_people,
        "man": pred_men,
        "woman": pred_women,
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

    p_p.append(pred["person"].strip().startswith("Yes"))
    m_p.append(pred["man"].strip().startswith("Yes"))
    w_p.append(pred["woman"].strip().startswith("Yes"))

report_p = classification_report(p_gt, p_p)
report_m = classification_report(m_gt, m_p)
report_w = classification_report(w_gt, w_p)

with open(output_dir / "moondream_qa_report.md", "w", encoding="utf-8") as f:
    f.write(
        f"""# MoonDream Evaluation Report


        ## Woman

        {report_w}

           ## Man

           {report_m}

            ## Person

            {report_p}


            """
    )
