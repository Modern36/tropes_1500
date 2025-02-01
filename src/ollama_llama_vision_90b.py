from trope_paths import raw_dir, ollam_tmp_dir, read_data
import ollama
from tqdm import tqdm


if __name__ == "__main__":

    data = read_data()

    dataw = data[data.apply(lambda x: x["gt_w"], axis=1)]
    datanw = data[data.apply(lambda x: not x["gt_w"], axis=1)]

    total = 3000
    each = int(total / 2)

    file_names = set(
        dataw["file_name"].to_list()[:each]
        + datanw["file_name"].to_list()[:each]
    )

    transactions = []
    for file_name in tqdm(file_names):
        out_name = file_name + ".jsonish"
        output_file = ollam_tmp_dir / out_name
        if output_file.exists():
            continue
        source_path = raw_dir / file_name
        transactions.append((source_path, output_file))

    for image, output in tqdm(transactions):

        response = ollama.chat(
            model="llama3.2-vision:90b",
            messages=[
                {
                    "content": 'I will show you an image, and i want you to tell me the following: whether there are people in the image, whether there is at least one man in the image and whether there is at least one woman in the image. I would prefer if you could reply in the following JSON-like format: {"people": <float>, "man": <float>, "woman": <float>}. The <float> represents how certain you are that the category is found in the image where 0.0 == 100% sure that the category is NOT in the image and 1.0 == 100% sure that the object IS in the image.Please do not add anything else to the answer.',
                    "role": "user",
                    "images": [str(image)],
                }
            ],
        )
        content = response.get("message").get("content")
        with open(output, "x", encoding="utf-8") as f:
            f.write(content)
