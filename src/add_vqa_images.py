from trope_paths import output_dir, raw_dir, read_data

df = read_data()

vqa_dir = output_dir / "vqa"
vqa_dir.mkdir(exist_ok=True)

vqa_file = vqa_dir / "vqa.md"

with open(vqa_file, "w") as f:
    f.write("## VQA\n")

    for idx, row in df.iterrows():
        file = row["file_name"]
        vqa_m = row["vqa_m"]
        vqa_w = row["vqa_w"]

        image_path = raw_dir / file

        if not image_path.exists():
            continue

        f.write(f"### {file}\n\n")
        f.write(f"![](/000_raw/{file})\n\n")
        f.write(f"Man: {vqa_m} -- Woman: {vqa_w}\n\n")
