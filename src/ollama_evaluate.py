from paths_20 import read_data, ollam_tmp_dir, output_dir
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


for file in ollam_tmp_dir.glob("*"):
    with open(file, "r") as f:
        data = f.read()
    data_dict = json.loads(data)
    outcome_dict[file.name[:-8]]["pred"] = {
        "person": data_dict["people"],
        "man": data_dict["man"],
        "woman": data_dict["woman"],
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
    p_p.append(pred["person"])
    m_p.append(pred["man"])
    w_p.append(pred["woman"])

report_p = classification_report(p_gt, p_p)
report_m = classification_report(m_gt, m_p)
report_w = classification_report(w_gt, w_p)

with open(output_dir / "ollama_report.md", "w", encoding="utf-8") as f:
    f.write(
        f"""# Ollama Evaluation Report

            Writing the reports in steps due to the classification taking ~10h and I want to be able to stop it if it turns out that it is not viable.

        ## Woman

        {report_w}

           ## Man

           {report_m}

            ## Person

            {report_p}


            """
    )
