from pathlib import Path

import pandas as pd

output_dir = Path(__file__).parents[1]
raw_dir = output_dir / "000_raw"
metadata_dir = output_dir / "metadata_jsons"

model_output = output_dir / "010_model_output"

ollama_desc_dir = model_output / "ollama_description_output"

ollam_tmp_dir = output_dir / "ollama_confidence_output"
ollam_tmp_dir.mkdir(parents=True, exist_ok=True)

detections = output_dir / "999_detect_data"
data_file = output_dir / "data.csv"


def read_data():
    return pd.read_csv(data_file, index_col=None)
