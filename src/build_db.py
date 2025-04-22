# Build db
import json
import re
import sqlite3

import pandas as pd

from browser_group_best_worst import calculate_groups
from trope_paths import (
    db_path,
    detections,
    metadata_dir,
    ollama_desc_dir,
    read_data,
)


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
            model = f"YOLO_{int(threshold * 100)}"
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


def load_yolo_objects(conn):
    for box_table in detections.glob("yolos-*.tsv"):
        image_id = box_table.name.split("_")[-1].split(".")[0]
        data = pd.read_csv(box_table, sep="\t")

        conn.executemany(
            f"insert into yolo (image_id, label, score) values ('{image_id}', ?, ?)",
            data[["label", "score"]].values.tolist(),
        )


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

        conn.execute(
            """
        CREATE table  yolo (
            image_id text,
            label,
            score
            )
            """
        )

        conn.execute("CREATE  index yolo_objects on yolo (image_id)")

        add_model_output(conn, load_ground_truth())

        add_model_output(conn, load_yolo())

        add_model_output(conn, load_dino())

        load_yolo_objects(conn)

        add_model_output(conn, load_vqa())

        add_model_output(conn, load_llama_desc())

        calculate_groups(conn)


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


def load_vqa():
    gt_data = read_data()

    for _, row in gt_data.iterrows():
        image_id = row["file_name"].split(".")[0]
        pred = {
            "m": row["vqa_m"],
            "w": row["vqa_w"],
        }
        pred["p"] = max(pred.values())

        for label, found in pred.items():
            yield {
                "image_id": image_id,
                "label": label,
                "model": "VQA",
                "found": found,
            }


def load_llama_desc():
    for desc_file in ollama_desc_dir.iterdir():
        image_id = desc_file.name.split(".")[0]
        with open(desc_file, "r", encoding="utf8") as f:
            text = f.read()
        m = len(re.findall(r"\bm[ae]n\b", text)) > 0
        w = len(re.findall(r"\bwom[ae]n\b", text)) > 0
        p = (
            m
            or w
            or (
                len(re.findall(r"\b(person|people)\b", text)) > 0
                and len(re.findall(r"no \b(person|people|individual)", text))
                == 0
            )
        )

        for label, outcome in (("m", m), ("w", w), ("p", p)):
            yield {
                "image_id": image_id,
                "label": label,
                "model": "llama-desc",
                "found": outcome,
                "desc": text,
            }
