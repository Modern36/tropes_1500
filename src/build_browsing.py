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
        add_metadata(conn)


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


# Create tree structure for .md files


if __name__ == "__main__":
    build_db()
