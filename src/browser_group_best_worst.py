import sqlite3
from collections import defaultdict

from build_db import build_db
from trope_paths import (
    browser_root,
    db_path,
    model_output,
    ollama_desc_dir,
    output_dir,
    raw_dir,
)


def group_images():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        image_ids = [
            image_id
            for image_id, *_ in cursor.execute("select image_id from images")
        ]

        for image_id in image_ids:
            outcome = {
                model + label: found
                for model, label, found in cursor.execute(
                    "select model, label, found from prediction where image_id = ?",
                    (image_id,),
                )
                if label in "mw"
            }
            key_cores = {key[:-1] for key in outcome}
            pairs = {
                key: (outcome[key + "m"], outcome[key + "w"])
                for key in key_cores
            }
            gt = pairs["GroundTruth"]
            del pairs["GroundTruth"]

            pair_to_names = defaultdict(set)
            for name, pair in pairs.items():
                pair_to_names[pair].add(name)

            if len(pair_to_names[gt]) == len(pair_to_names):
                yield image_id, "AllGood"
            elif len(pair_to_names[gt]) == 0:
                yield image_id, "AllBad"
            elif len(pair_to_names[gt]) == 1:
                model, *_ = pair_to_names[gt]
                yield image_id, f"Good_{model}"
            elif len(pair_to_names[gt]) == len(pair_to_names) - 1:
                model = [key for key, item in pairs.items() if item != gt][0]
                yield image_id, f"Bad_{model}"


def main():
    # table

    groups = group_images()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "create table if not exists gathering ("
            "image_id text primary key,"
            "group_name text"
            ")"
        )

        # calculate grps
        cursor.executemany(
            "insert into gathering (image_id, group_name) values (?, ?)",
            groups,
        )
