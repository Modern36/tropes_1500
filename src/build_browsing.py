import sqlite3
from pathlib import Path

from sklearn.metrics import classification_report

from browser_group_best_worst import write_gathered_readmes
from build_db import build_db
from trope_paths import (
    browser_root,
    db_path,
    ollama_desc_dir,
    output_dir,
    raw_dir,
    resolve_image_path,
)


def remove_directory_tree(path: Path = browser_root):
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            remove_directory_tree(child)
    path.rmdir()


def calculate_report(conn, model, collection=None):
    query = "select found from prediction "
    if collection:
        query += "join images on prediction.image_id == images.image_id "
    query += "where model == :model and label == :label "
    if collection:
        query += " and collection_name == :collection_name"

    query += " order by prediction.image_id"

    str_report = "\n\n\n"

    for label in "wmp":
        gt = [
            label
            for label, *_ in conn.execute(
                query,
                {
                    "collection_name": collection,
                    "model": "GroundTruth",
                    "label": label,
                },
            )
        ]
        pred = [
            label
            for label, *_ in conn.execute(
                query,
                {
                    "collection_name": collection,
                    "model": model,
                    "label": label,
                },
            )
        ]

        if len(gt) == len(pred) and len(set(gt) | set(pred)) > 1:
            label_report = classification_report(gt, pred, zero_division=False)

            str_report += f"""

## Label: {label}

```
{label_report}
```

"""
    return str_report


def tabulate_objects(conn, model, collection):
    if not model.startswith("YOLO"):
        return ""
    threshold = float(model.split("_")[-1]) / 100
    query = (
        "select label, count(yolo.image_id) as items, "
        "count(distinct yolo.image_id) as images from yolo "
    )
    if collection:
        query += (
            "join images on yolo.image_id == images.image_id "
            " and collection_name == :collection_name "
        )
    query += f" where score >= {threshold} "
    query += "group by label order by items desc, images desc"

    cursor = conn.execute(query, {"collection_name": collection})
    results = cursor.fetchall()
    table_string = "| Label | Items | Images |\n|:--- | ---:| ---:|\n"
    for label, items, images in results:
        table_string += f"| {label} | {items} | {images} |\n"

    return table_string


# Create tree structure for .md files
def build_tree():
    # First we remove the old
    remove_directory_tree()

    # And re-create:
    browser_root.mkdir()

    with sqlite3.connect(db_path) as conn:
        models = {
            _[0]
            for _ in conn.execute(
                "select distinct model from prediction"
            ).fetchall()
        } - {
            "GroundTruth",
        }
        collections = (
            [(None, None)]
            + list(
                set(
                    conn.execute(
                        "select distinct collection_owner_name, collection_name from images"
                    ).fetchall()
                )
            )
            + []
        )
        for model in models:
            model_dir = browser_root / model.replace(" ", "_")
            model_dir.mkdir()
            for collection in collections:
                if collection[0] is None:
                    collection_str = "1500_ALL"
                else:
                    collection_str = "_".join(collection).replace(" ", "_")
                coll_dir = model_dir / collection_str
                coll_dir.mkdir()

                image_count = len(list(get_images(conn, model, collection[1])))

                report = calculate_report(
                    conn, model=model, collection=collection[1]
                )

                objects_table = tabulate_objects(
                    conn, model=model, collection=collection[1]
                )

                # Create a README.md file for each collection directory
                readme_path = coll_dir / "README.md"
                with open(readme_path, "w") as f:
                    f.write(f"# Collection: {collection[1]}\n")
                    f.write(f"Owner: {collection[0]}\n\n")
                    f.write(
                        f"This file contains {image_count} images processed by the model: {model}\n"
                    )

                    f.write(report)

                    f.write(objects_table)

                    if model == "VQA":
                        f.write(
                            """
## VQA
#### Men
 - How many adult males are depicted in the image?
 - Is there at least one adult male in the image?
 - Is there an adult male in the image?
 - How many adult males are depicted in the photograph?
 - Is there at least one adult male in the photograph?
 - Is there an adult male in the photograph?
 - A man somewhere?

#### Women
 - How many adult females are depicted in the image?
 - Is there at least one adult female in the image?
 - Is there an adult female in the image?
 - How many adult females are depicted in the photograph?
 - Is there at least one adult female in the photograph?
 - Is there an adult female in the photograph?
 - A woman somewhere?


"""
                        )

                    for image_data in get_images(conn, model, collection[1]):
                        f.write(image_data_to_str(*image_data, model=model))
            readme_path = model_dir / "README.md"
            with open(readme_path, "w") as f:
                f.write(f"# Collection: {model}\n")
                f.write(
                    f"This file contains {1500} images processed by the model: {model}\n"
                )

                for image_data in get_images(conn, model):
                    f.write(image_data_to_str(*image_data, model=model))


def get_images(conn, model, collection_name=None):
    if collection_name is not None:
        query = (
            "select * from images where collection_name == :collection_name"
        )
    else:
        query = "select * from images"
    for image_row in conn.execute(
        query,
        {"collection_name": collection_name},
    ):
        image_id, *_ = image_row
        gt = {
            label: found
            for label, found in conn.execute(
                "select label, found from prediction where image_id == :image_id and model == :model",
                {
                    "image_id": image_id,
                    "model": "GroundTruth",
                },
            )
        }
        pred = {
            label: found
            for label, found in conn.execute(
                "select label, found from prediction where image_id == :image_id and model == :model",
                {
                    "image_id": image_id,
                    "model": model,
                },
            )
        }
        yield image_id, gt, pred


emojis = {0: "🟥", 1: "🟢"}


def image_data_to_str(image: str, gt: dict, pred: dict, model):
    # temporary going to default image
    image_loc = resolve_image_path(image, model)

    relative_loc = image_loc.relative_to(output_dir)

    if not relative_loc.exists():
        raise Warning(f"{image_loc.relative_to(raw_dir)} does not exist")

    result = f"""

## {image}

![{relative_loc}](/{relative_loc})
"""

    result += """\n
| label | GT | Pred | accurate |
|:----|----|----|----|"""

    for label, short_label in [
        ("Man", "m"),
        ("Woman", "w"),
        ("Person", "p"),
    ]:
        if short_label in pred.keys():
            ground = gt[short_label]
            prediction = pred[short_label]
            marker = emojis[ground == prediction]
            result += f"""
| {label} | {ground} | {prediction} | {marker} |"""
    if model == "llama-desc":
        with open(
            ollama_desc_dir / (image + ".png.txt"), "r", encoding="utf8"
        ) as f:
            result += "\n\n```"
            result += f.read()
            result += "\n```\n"

    return result + "\n\n\n"


if __name__ == "__main__":
    build_db()

    build_tree()
    write_gathered_readmes()
