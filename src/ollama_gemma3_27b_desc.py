import ollama
from tqdm import tqdm

from trope_paths import gemma3_desc_dir, raw_dir, read_data

if __name__ == "__main__":

    data = read_data()

    dataw = data[data.apply(lambda x: x["gt_w"], axis=1)]
    datanw = data[data.apply(lambda x: not x["gt_w"], axis=1)]

    total = 100
    each = int(total / 2)

    file_names = set(
        dataw["file_name"].to_list()[:each]
        + datanw["file_name"].to_list()[:each]
    )

    transactions = []
    for file_name in tqdm(file_names):
        out_name = file_name + ".txt"
        output_file = gemma3_desc_dir / out_name
        if output_file.exists():
            continue
        source_path = raw_dir / file_name
        transactions.append((source_path, output_file))

    for image, output in tqdm(transactions):

        response = ollama.chat(
            model="gemma3:27b",
            messages=[
                {
                    "content": " I will show you an photograph from a "
                    "historical collection, please describe the people in "
                    "as much detail as you can. I am particularly interested "
                    "whether they are men, women or children. If it is "
                    "impossible to determine, refer to them as 'person' or "
                    "'people'. People may appear anywhere in the picture, "
                    "and may be out of focus. Since they are not necessarily "
                    "the focus of the image they may be partially hidden "
                    "objects or not be completely included in the phogograph. "
                    "Remember to include people that are in the background, "
                    "and people that are out of focus. Sometimes the only way "
                    "to distinguish between genders is by their clothing.",
                    "role": "user",
                    "images": [str(image)],
                }
            ],
        )
        content = response.get("message").get("content")
        with open(output, "x", encoding="utf-8") as f:
            f.write(content)
