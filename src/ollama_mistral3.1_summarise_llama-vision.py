import json
from random import shuffle

import ollama
from pydantic import BaseModel
from tqdm import tqdm

from trope_paths import mistral_summary_dir, ollama_desc_dir


class Description(BaseModel):
    woman: bool
    woman_reasoning: str
    man: bool
    man_reasoning: str
    person: bool
    person_reasoning: str


if __name__ == "__main__":
    source_files = list(ollama_desc_dir.glob("*.txt"))

    assert len(source_files) == 1500

    mistral_summary_dir.mkdir(exist_ok=True)

    transactions = [
        (
            source_path,
            out_path,
        )
        for source_path in source_files
        if not (
            out_path := mistral_summary_dir
            / source_path.name.replace(".txt", ".json")
        ).exists()
    ]

    shuffle(transactions)

    for source_path, out_path in tqdm(transactions):
        with open(source_path, "r", encoding="utf-8") as f:
            description = f.read()

        response = ollama.chat(
            model="mistral-small3.1:24b",
            messages=[
                {
                    "content": "Summarize the following image-descriptions in"
                    " terms of the people found. There are three categories:"
                    ' "Woman", "Man" and "Person". If people are mentioned,'
                    ' but it is not clear whether it belongs to "Woman" or '
                    '"Man, they count as "Person". If it is explicitly '
                    'mentioned that no "Woman", "Man" and "Person" are mentioned,'
                    ' the response is "0". If a man or a woman is mentioned -- '
                    " this also counts as a person being mentioned. Provide "
                    "a reasoning for each category. Reply in JSON format. \n\n"
                    f'"""\n\n" + {description} + "\n\n"""\n\n',
                    "role": "user",
                }
            ],
            format=Description.model_json_schema(),
        )
        content = response.get("message").get("content")

        country = Description.model_validate_json(content)

        country = json.loads(country.model_dump_json())
        if country["person"] == 0 and (country["woman"] + country["man"]) > 0:
            raise ValueError(
                "No 'Women' or 'Men' found in the image description."
            )

        with open(out_path, "x", encoding="utf-8") as f:
            f.write(content)
