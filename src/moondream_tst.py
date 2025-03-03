"""
Download model: https://huggingface.co/vikhyatk/moondream2/resolve/9dddae84d54db4ac56fe37817aeaeb502ed083e2/moondream-2b-int8.mf.gz?download=true
"""

import moondream as md
from PIL import Image
from trope_paths import moondream_model, output_dir
from trope_paths import raw_dir, moon_tmp_dir, read_data
from tqdm import tqdm
import json

# Initialize with local model path. Can also read .mf.gz files, but we recommend decompressing
# up-front to avoid decompression overhead every time the model is initialized.
model = md.vl(model=str(moondream_model))

# Load and process image
image = Image.open(output_dir / "DinoWomanMan_th25/022yi14dr7qw.png")
encoded_image = model.encode_image(image)

# Generate caption
caption = model.caption(encoded_image)["caption"]
print("Caption:", caption)

# Ask questions
answer = model.query(encoded_image, "What's in this image?")["answer"]
print("Answer:", answer)

if __name__ == "__main__":

    data = read_data()

    dataw = data[data.apply(lambda x: x["gt_w"], axis=1)]
    datanw = data[data.apply(lambda x: not x["gt_w"], axis=1)]

    total = 20
    each = int(total / 2)

    file_names = set(
        dataw["file_name"].to_list()[:each]
        + datanw["file_name"].to_list()[:each]
    )

    transactions = []
    for file_name in tqdm(file_names):
        out_name = file_name + ".json"
        output_file = moon_tmp_dir / out_name
        if output_file.exists():
            continue
        source_path = raw_dir / file_name
        transactions.append((source_path, output_file))

    for image, output in tqdm(transactions):

        imagef = Image.open(output_dir / "DinoWomanMan_th25/022yi14dr7qw.png")
        encoded_image = model.encode_image(imagef)

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
