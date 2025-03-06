from m36_utils.detectors import GrounDino, YolosBase

from trope_paths import data_file, detections, raw_dir, read_data, model_output


class DinoManWoman(GrounDino):
    def __init__(self):
        categories = ("man", "woman")
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoManWoman"


class DinoMan(GrounDino):
    def __init__(self):
        categories = ("man",)
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoMan"


class DinoWoman(GrounDino):
    def __init__(self):
        categories = ("woman",)
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoWoman"


class DinoWomanMan(GrounDino):
    def __init__(self):
        categories = ("woman", "man")
        super().__init__(categories=categories)

    def __str__(self):
        return "DinoWomanMan"


class YolosPretrained(YolosBase):
    def __str__(self):
        return "yolos-pretrained"


def draw_images():

    def yolo_base():
        yolopre = YolosPretrained()
        yolopre.mode = "count|save"
        yolopre.box_scores = True
        yolopre.process_dir(
            input_dir=raw_dir,
            thresholds=[0.5, 0.75, 0.9],
            output_dir=model_output,
        )

    def dino_four():
        for dino in [
            DinoManWoman(),
            DinoWomanMan(),
            DinoMan(),
            DinoWoman(),
        ]:
            dino.mode = "count|save"
            dino.box_scores = True
            dino.process_dir(
                input_dir=raw_dir, thresholds=[0.25], output_dir=model_output
            )

    def collect_tsv_files():
        for tsv in model_output.glob("*.tsv"):
            new_path = detections / tsv.name
            tsv.rename(new_path)

    # yolo_base()
    dino_four()

    collect_tsv_files()


def load_data():
    try:
        return read_data()
    except FileNotFoundError:
        create_data()
    return read_data()


def create_data():
    df = read_data()

    file_paths = list(raw_dir.glob("*"))

    df = add_dino_manwoman(df, file_paths)

    df = add_dino_womanman(df, file_paths)

    df = add_dino_man(df, file_paths)

    df = add_dino_woman(df, file_paths)

    df = add_yolo_person(df, file_paths, threshold=0.5)
    df = add_yolo_person(df, file_paths, threshold=0.75)
    df = add_yolo_person(df, file_paths, threshold=0.9)

    df.to_csv(data_file, index=False)


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


def add_dino_man(df, file_paths, force=False):

    if force or "dm_m" not in df.columns:

        dinomw = DinoMan()
        dinomw.mode = ""

        dino_mw_p = dinomw.predict(file_paths, threshold=0.25)
        df["dm_m"] = dino_mw_p["man"]

    return df


def add_dino_woman(df, file_paths, force=False):

    if force or "dw_m" not in df.columns:

        dinowm = DinoWoman()
        dinowm.mode = ""

        dino_mw_p = dinowm.predict(file_paths, threshold=0.25)
        df["dw_w"] = dino_mw_p["woman"]

    return df


def add_yolo_person(df, file_paths, threshold, force=False):

    if force or "yolo_p" not in df.columns:

        yolo = YolosPretrained()
        yolo.mode = ""
        yolo_p_p = yolo.predict(file_paths, threshold=threshold)
        df["yolo_p"] = yolo_p_p["person"]

    return df


if __name__ == "__main__":

    draw_images()
