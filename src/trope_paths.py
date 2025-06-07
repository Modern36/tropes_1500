from pathlib import Path

import pandas as pd

output_dir = Path(__file__).parents[1]
raw_dir = output_dir / "000_raw"
metadata_dir = output_dir / "metadata_jsons"

model_output = output_dir / "010_model_output"

ollama_desc_dir = model_output / "ollama_description_output"

mistral_summary_dir = model_output / "mistral_summary_llama-vision"

ollam_tmp_dir = output_dir / "ollama_confidence_output"

moon_tmp_dir = output_dir / "moon_point_output"

moon_tmp_qa = model_output / "moon_QA_output"


detections = output_dir / "999_detect_data"
data_file = output_dir / "data.csv"

browser_root = output_dir / "browser"
moondream_model = output_dir / "moondreammodel" / "moondream-2b-int8.mf"
scatter_file = browser_root / "scatter.md"
scatter_data_file = output_dir / "scatter_data.csv"


def read_data():
    return pd.read_csv(data_file, index_col=None)


db_path = output_dir / "db.sqlite3"


browser_gathering = browser_root / "gathering"
model_to_subdir = {
    "DinoManWoman": model_output / "DinoManWoman_th25",
    "DinoWomanMan": model_output / "DinoWomanMan_th25",
    "DinoManWoman2": model_output / "DinoManWoman_th25",
    "DinoWomanMan2": model_output / "DinoWomanMan_th25",
    "YOLO_50": model_output / "yolos-pretrained_th50",
    "YOLO_75": model_output / "yolos-pretrained_th75",
    "YOLO_90": model_output / "yolos-pretrained_th90",
    "VQA": raw_dir,
    "llama-desc": model_output / "ollama_description_output",
}


def resolve_image_path(image, model):
    image_dir = model_to_subdir[model]

    image_loc = image_dir / (image + ".png")
    if image_loc.exists():
        return image_loc

    if model == "YOLO_50":
        return resolve_image_path(image, "YOLO_75")
    elif model == "YOLO_75":
        return resolve_image_path(image, "YOLO_90")
    else:
        return raw_dir / (image + ".png")
