from trope_paths import (
    raw_dir,
    metadata_dir,
    output_dir,
    read_data,
    detections,
    browser_root,
    model_output,
)
import sqlite3
import json
import pandas as pd
from pathlib import Path

db_path = output_dir / "db.sqlite3"


# Build db
def build_db():
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
        CREATE TABLE images (
            image_id TEXT PRIMARY KEY,
            url TEXT,
            photographer TEXT,
            unique_id TEXT,
            type TEXT,
            title TEXT,
            place_of_production TEXT,
            year_from INTEGER,
            year_to INTEGER,
            producer TEXT,
            motif TEXT,
            artifact_owner INTEGER,
            collection_id INTEGER,
            collection_name TEXT,
            uuid TEXT,
            collection_owner_name TEXT)
        """
        )
        add_metadata(conn)

        conn.execute(
            """
        CREATE TABLE prediction (
            prediciton_id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT not null,
            model TEXT not null,
            label text not null,
            found bool not null)
            """
        )
        conn.execute(
            """
        CREATE UNIQUE INDEX unique_prediction ON prediction (
            image_id,
            model,
            label,
            found)
            """
        )

        add_model_output(conn, load_ground_truth())

        add_model_output(conn, load_yolo())

        add_model_output(conn, load_dino())

    # TODO: Add Llama-vision output
    # TODO: Add Moondream output


def load_metadata():
    for filename in metadata_dir.glob("*.json"):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            yield {
                "image_id": data["image_id"],
                "url": data["url"],
                "photographer": data["photographer"],
                "unique_id": data["unique_id"],
                "type": data["type"],
                "title": data["title"],
                "place_of_production": data["place_of_production"],
                "year_from": data["year_from"],
                "year_to": data["year_to"],
                "producer": data["producer"],
                "motif": data["motif"],
                "artifact_owner": data["artifact_owner"],
                "collection_id": data["collection_id"],
                "collection_name": data["collection_name"],
                "uuid": data["uuid"],
                "collection_owner_name": data["collection_owner_name"],
            }


def add_metadata(db: sqlite3.Connection):
    db.executemany(
        """
            INSERT INTO images (
                image_id,
                url,
                photographer,
                unique_id,
                type,
                title,
                place_of_production,
                year_from,
                year_to,
                producer,
                motif,
                artifact_owner,
                collection_id,
                collection_name,
                uuid,
                collection_owner_name
            ) VALUES (
                :image_id,
                :url,
                :photographer,
                :unique_id,
                :type,
                :title,
                :place_of_production,
                :year_from,
                :year_to,
                :producer,
                :motif,
                :artifact_owner,
                :collection_id,
                :collection_name,
                :uuid,
                :collection_owner_name
            )
        """,
        load_metadata(),
    )


def add_model_output(conn, model_output):
    conn.executemany(
        """
        INSERT INTO prediction (
            image_id,
            model,
            label,
            found
        ) VALUES (
            :image_id,
            :model,
            :label,
            :found
        )
    """,
        model_output,
    )


def load_ground_truth():
    gt_data = read_data()

    for _, row in gt_data.iterrows():
        image_id = row["file_name"].split(".")[0]
        for label in "mwp":
            yield {
                "image_id": image_id,
                "label": label,
                "model": "GroundTruth",
                "found": row[f"gt_{label}"],
            }


def load_yolo():
    for box_table in detections.glob("yolos-*.tsv"):
        image_id = box_table.name.split("_")[-1].split(".")[0]
        data = pd.read_csv(box_table, sep="\t")
        data = data[data.label == "person"]
        for threshold in [0.5, 0.75, 0.9]:
            data = data[data.score >= threshold]
            model = f"YOLO_{int(threshold *100)}"
            yield {
                "image_id": image_id,
                "label": "p",
                "model": model,
                "found": len(data) > 0,
            }


def load_dino():
    for dino_box_table in detections.glob("Dino*_*.tsv"):
        model, image = dino_box_table.name.split("_")
        image_id = image.split(".")[0]
        with open(dino_box_table, "r", encoding="utf8") as f:
            data = f.read()
        labels = [_.lower() for _ in ["Man", "Woman"] if _ in model]
        assert len(labels) in (1, 2)
        predictions = {label: f'"{label}"' in data for label in labels}
        predictions["person"] = max(predictions.values())

        for key, value in predictions.items():
            yield {
                "image_id": image_id,
                "label": key[0],
                "model": model,
                "found": value,
            }


def remove_directory_tree(path: Path = browser_root):
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            remove_directory_tree(child)
    path.rmdir()


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
        collections = set(
            conn.execute(
                "select distinct collection_owner_name, collection_name from images"
            ).fetchall()
        )
        for model in models:
            model_dir = browser_root / model.replace(" ", "_")
            model_dir.mkdir()
            image_dir = model_to_subdir[model]
            for collection in collections:
                collection_str = "_".join(collection).replace(" ", "_")
                coll_dir = model_dir / collection_str
                coll_dir.mkdir()

                image_count = len(list(get_images(conn, model, collection[1])))

                # Create a README.md file for each collection directory
                readme_path = coll_dir / "README.md"
                with open(readme_path, "w") as f:
                    f.write(f"# Collection: {collection[1]}\n")
                    f.write(f"Owner: {collection[0]}\n\n")
                    f.write(
                        f"This file contains {image_count} images processed by the model: {model}\n"
                    )

                    for image_data in get_images(conn, model, collection[1]):
                        f.write(
                            image_data_to_str(*image_data, image_dir=image_dir)
                        )


def get_images(conn, model, collection_name):
    for image_row in conn.execute(
        "select * from images where collection_name == :collection_name",
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


model_to_subdir = {
    "DinoManWoman": model_output / "DinoManWoman_th25",
    "DinoWomanMan": model_output / "DinoWomanMan_th25",
    "DinoMan": model_output / "DinoMan_th25",
    "DinoWoman": model_output / "DinoWoman_th25",
    "YOLO_50": model_output / "yolos-pretrained_th50",
    "YOLO_75": model_output / "yolos-pretrained_th75",
    "YOLO_90": model_output / "yolos-pretrained_th90",
}

emojis = {0: "🟥", 1: "🟢"}


def image_data_to_str(image: str, gt: dict, pred: dict, image_dir: Path):
    # temporary going to default image
    image_loc = image_dir / (image + ".png")
    relative_loc = image_loc.relative_to(output_dir)

    result = f"""

## {image}

![This is an image](/{relative_loc})

| label | GT | Pred | accurate |
|:----|----|----|----|"""
    for label, l in [
        ("Man", "m"),
        ("Woman", "w"),
        ("Person", "p"),
    ]:
        if l in pred.keys():
            ground = gt[l]
            prediction = pred[l]
            marker = emojis[ground == prediction]
            result += f"""
| {label} | {ground} | {prediction} | {marker} |"""
    return result + "\n\n\n"


if __name__ == "__main__":
    build_db()

    build_tree()
