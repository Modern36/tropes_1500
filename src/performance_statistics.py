from classification_report_md import markdown_class_report

from paths_20 import output_dir, read_data

headers = {
    "vqa": "ViLT-VQA",
    "dmw": "GroundingDino - Man Woman",
    "dwm": "GroundingDino - Woman Man ",
    "m": "men",
    "w": "women",
    "p": "person",
    "yolo": "YOLO",
}


def write_matrices(df, subdir_name):
    stat_dir = output_dir / "statistics" / subdir_name
    stat_dir.mkdir(exist_ok=True, parents=True)

    for model_abbrev in ("vqa", "dmw", "dwm", "yolo"):
        if model_abbrev == "yolo":
            genders = ("p",)
        else:
            genders = ("m", "w")

        stat_file = stat_dir / (model_abbrev + ".md")

        with open(stat_file, "w", encoding="utf-8") as f:
            f.write(f"# {headers[model_abbrev]}\n\n")

        for gender in genders:
            gt = df["gt_" + gender]
            pred = df[model_abbrev + "_" + gender]
            report = markdown_class_report(y_true=gt, y_pred=pred)

            with open(stat_file, "a", encoding="utf-8") as f:
                f.write(f"## {headers[gender]}\n\n")
                f.write(report)
                f.write("\n\n")


def calculate_statistics():
    df = read_data()

    write_matrices(df[df.set_20].copy(), "20_picked")

    write_matrices(df.copy(), "overall")


if __name__ == "__main__":
    calculate_statistics()
