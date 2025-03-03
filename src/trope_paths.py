from pathlib import Path

import pandas as pd

output_dir = Path(__file__).parents[1]
raw_dir = output_dir / "000_raw"
metadata_dir = output_dir / "metadata_jsons"

ollam_tmp_dir = output_dir / "ollama_confidence_output"
ollam_tmp_dir.mkdir(parents=True, exist_ok=True)

detections = output_dir / "999_detect_data"
data_file = output_dir / "data.csv"

moondream_model = output_dir / "moondreammodel" / "moondream-2b-int8.mf"


def read_data():
    return pd.read_csv(data_file, index_col=None)
