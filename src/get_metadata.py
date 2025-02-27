from m36_utils.databases.base import database_path
import sqlite3
from trope_paths import raw_dir, metadata_dir
import json


def get_metadata_dict(image_id):
    with sqlite3.connect(database=database_path, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "select * from image as i join image_artifact_through as ia on i.image_id == ia.image_id join artifact as a on a.unique_id == ia.artifact_id join collection_artifact_through as ca on ca.artifact_id == a.unique_id join collection as c on c.id == ca.collection_id where i.image_id == :image_id",
            {"image_id": image_id},
        )
    return dict(cursor.fetchone())


def collect_metadata(force=False):
    for image in raw_dir.iterdir():
        out_file = metadata_dir / image.with_suffix(".json").name
        if out_file.exists() and not force:
            continue

        item_dict = get_metadata_dict(image.with_suffix("").name)

        with open(out_file, "wx"[force], encoding="utf-8") as f:
            json.dump(item_dict, f)


if __name__ == "__main__":
    collect_metadata(force=False)
