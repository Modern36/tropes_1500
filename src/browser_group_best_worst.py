import sqlite3
from collections import defaultdict

from trope_paths import (
    browser_gathering,
    db_path,
    output_dir,
    resolve_image_path,
)


def group_images(conn):
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
            key: (outcome[key + "m"], outcome[key + "w"]) for key in key_cores
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


def calculate_groups(conn):
    # table

    groups = group_images(conn)

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


def write_gathered_readmes():
    legend = """
| icon | GroundTruth |
|:----|------------|
|🚷| No women or men annotated|
|🚹| At least one man, but no women|
|🚺| At least one woman, but no men|
|🚻| At least one man and woman|\n\n"""

    browser_gathering.mkdir(exist_ok=True)

    grp_to_images = defaultdict(set)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for image, grp_name in cursor.execute(
            "select image_id, group_name from gathering"
        ):
            grp_to_images[grp_name].add(image)

        for grp_name in grp_to_images.keys():
            images = sorted(grp_to_images[grp_name])

            out_path = browser_gathering / f"{grp_name}.md"

            with open(out_path, "w") as f:
                f.write(f"# {grp_name}\n\n")

                f.write(legend)

                for image in images:
                    icon = get_image_icon(cursor, image)

                    image_loc = resolve_image_path(image, "VQA")

                    relative_loc = image_loc.relative_to(output_dir)

                    f.write(
                        f"## {image} - {icon}\n\n![{relative_loc}](/{relative_loc})\n\n"
                    )


def get_image_icon(cursor, image):
    parking = {
        label: found
        for label, found in cursor.execute(
            'select label, found from prediction where image_id == ? and model == "GroundTruth"',
            (image,),
        )
    }

    index = parking["m"] + parking["w"] * 2

    icon = "🚷🚹🚺🚻"[index]
    return icon
