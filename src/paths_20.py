from pathlib import Path

import pandas as pd

output_dir = Path(__file__).parents[1]
raw_dir = output_dir / "000_raw"
detections = output_dir / "999_detect_data"
data_file = output_dir / "data.csv"


def read_data():
    return pd.read_csv(data_file, index_col=None)
