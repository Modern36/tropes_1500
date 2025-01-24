from m36_utils.databases.image_files import collect_images
from m36_utils.detectors import GrounDino, YolosBase
from ml_data.files import get_clean_gender_df
from paths import get_image_path

from paths_20 import data_file, detections, output_dir, raw_dir, read_data
from performance_statistics import calculate_statistics
from yolo_performance import add_gtp


class DinoManWoman(GrounDino):
    def __init__(self):
        categories = ("man", "woman")
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoManWoman"


class DinoWomanMan(GrounDino):
    def __init__(self):
        categories = ("woman", "man")
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoWomanMan"


class YolosPretrained(YolosBase):
    def __str__(self):
        return "yolos-pretrained"


def image_ids():
    with open(output_dir / "20_images.txt", "r", encoding="utf8") as f:
        for line in f.readlines():
            yield line.strip()


def draw_images():

    collect_images(image_ids(), raw_dir, mode="copy")

    def yolo_base():
        yolopre = YolosPretrained()
        yolopre.mode = "count|save"
        yolopre.box_scores = True
        yolopre.process_dir(
            input_dir=raw_dir, thresholds=[0.75], output_dir=output_dir
        )

    def dino_both():
        for dino in [
            DinoManWoman(),
            DinoWomanMan(),
        ]:
            dino.mode = "count|save"
            dino.box_scores = True
            dino.process_dir(
                input_dir=raw_dir, thresholds=[0.25], output_dir=output_dir
            )

    def collect_tsv_files():
        for tsv in output_dir.glob("*.tsv"):
            new_path = detections / tsv.name
            tsv.rename(new_path)

    yolo_base()
    dino_both()

    collect_tsv_files()


def load_data():
    try:
        return read_data()
    except FileNotFoundError:
        create_data()
    return read_data()


def create_data():
    try:
        df = read_data()
    except FileNotFoundError:

        df = get_clean_gender_df()

        df.rename(
            {
                "groundtruth_man": "gt_m",
                "groundtruth_woman": "gt_w",
                "predicted_man": "vqa_m",
                "predicted_woman": "vqa_w",
            },
            axis="columns",
            inplace=True,
        )

        df["set_20"] = False
        for image in image_ids():
            filename = image + ".png"
            row_idx = df[df.file_name == filename].index
            df.loc[row_idx, "set_20"] = True

    file_paths = [get_image_path(filename) for filename in df.file_name]

    df = add_dino_manwoman(df, file_paths)

    df = add_dino_womanman(df, file_paths)

    df = add_yolo_person(df, file_paths)

    df.to_csv(data_file, index=False)

    add_gtp()


def add_dino_manwoman(df, file_paths, force=False):

    if force or "dmw_m" not in df or "dmw_m" not in df.columns:

        dinomw = DinoManWoman()
        dinomw.mode = ""

        dino_mw_p = dinomw.predict(file_paths, threshold=0.25)
        df["dmw_m"] = dino_mw_p["man"]
        df["dmw_w"] = dino_mw_p["woman"]

    return df


def add_dino_womanman(df, file_paths, force=False):

    if force or "dwm_m" not in df or "dwm_w" not in df.columns:

        dinowm = DinoWomanMan()
        dinowm.mode = ""

        dino_mw_p = dinowm.predict(file_paths, threshold=0.25)
        df["dwm_m"] = dino_mw_p["man"]
        df["dwm_w"] = dino_mw_p["woman"]

    return df


def add_yolo_person(df, file_paths, force=False):

    if force or "yolo_p" not in df.columns:

        yolo = YolosPretrained()
        yolo.mode = ""
        yolo_p_p = yolo.predict(file_paths, threshold=0.75)
        df["yolo_p"] = yolo_p_p["person"]

    return df


if __name__ == "__main__":
    raw_dir.mkdir()
    detections.mkdir()

    draw_images()

    calculate_statistics()
