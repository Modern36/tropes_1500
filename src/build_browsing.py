from trope_paths import raw_dir, metadata_dir, output_dir
import sqlite3
import json

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
    add_metadata(db_path)


def load_metadata():
    for filename in metadata_dir.glob("*.json"):
        with open(filename, "r", encoding="utf-8") as f:
            yield json.load(f)


def add_metadata(db_path):
    with sqlite3.connect(db_path) as db:
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


# Create tree structure for .md files


if __name__ == "__main__":
    build_db()
