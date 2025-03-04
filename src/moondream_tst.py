"""
Download model: https://huggingface.co/vikhyatk/moondream2/resolve/9dddae84d54db4ac56fe37817aeaeb502ed083e2/moondream-2b-int8.mf.gz?download=true
"""

import moondream as md
from PIL import Image
from trope_paths import moondream_model, output_dir
from trope_paths import raw_dir, moon_tmp_dir, read_data, moon_tmp_qa
from tqdm import tqdm
import json

if __name__ == "__main__":
    model = md.vl(model=str(moondream_model))

    data = read_data()

    dataw = data[data.apply(lambda x: x["gt_w"], axis=1)]
    datanw = data[data.apply(lambda x: not x["gt_w"], axis=1)]

    total = 7500
    each = int(total / 2)

    file_names = set(
        dataw["file_name"].to_list()[:each]
        + datanw["file_name"].to_list()[:each]
    )

    transactions = []
    for file_name in tqdm(file_names):
        out_name = file_name + ".json"
        output_file = moon_tmp_dir / out_name
        output_desc = moon_tmp_qa / out_name
        if output_file.exists() and output_desc.exists():
            continue
        source_path = raw_dir / file_name
        transactions.append((source_path, output_file, output_desc))

    for image, output, out2 in tqdm(transactions):

        imagef = Image.open(image)
        encoded_image = model.encode_image(imagef)

        if not output.exists():
            men = model.point(encoded_image, "men")["points"]
            women = model.point(encoded_image, "women")["points"]
            people = model.point(encoded_image, "people")["points"]

            content = {
                "people": len(people),
                "man": len(men),
                "woman": len(women),
            }

            with open(output, "x", encoding="utf-8") as f:
                f.write(json.dumps(content))

        if not out2.exists():
            men = model.query(
                encoded_image, "Are there any men in the photograph?"
            )["answer"]
            women = model.query(
                encoded_image, "Are there any women in the photograph?"
            )["answer"]
            people = model.query(
                encoded_image, "Are there any people in the photograph?"
            )["answer"]

            content = {
                "people": people,
                "man": men,
                "woman": women,
            }

            with open(out2, "x", encoding="utf-8") as f:
                f.write(json.dumps(content))
