from trope_paths import raw_dir, ollam_tmp_dir, read_data
import ollama
from tqdm import tqdm


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
        out_name = file_name + ".txt"
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
                    "content": " I will show you an image, please describe the people in "
                    "as much detail as you can. I am particularly interested "
                    "whether they are men, women or children. If it is "
                    "impossible to determine, refer to them as 'person' or "
                    "'people'.",
                    "role": "user",
                    "images": [str(image)],
                }
            ],
        )
        content = response.get("message").get("content")
        with open(output, "x", encoding="utf-8") as f:
            f.write(content)
