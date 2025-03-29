import sqlite3

from trope_paths import db_path, scatter_file


def make_scatterplot(cursor, Collection=None, c=1500):
    query = (
        "select model, "
        "sum(case when label == 'm' then found else 0 end) as m, "
        "sum(case when label == 'w' then found else 0 end) as f, "
        "count(distinct prediction.image_id) "
        "from prediction "
    )

    if Collection is not None:
        query += (
            "join images on prediction.image_id == images.image_id "
            f"where collection_name = '{Collection}' "
        )

    query += "group by model"

    if Collection is None:
        Collection = f"ALL {c}"

    md = f"""

```mermaid
quadrantChart
    title Men and women in {Collection}
    x-axis Percent --> Men
    y-axis Percent --> Women
"""

    for l, m, f, c in cursor.execute(query):
        if m == f == 0:
            continue
        M = m / c
        F = f / c
        md += f"    {l}: [{M}, {F}]"
        if l == "GroundTruth":
            md += " color: #00FF00"
        elif l.startswith("Dino"):
            md += " color: #999900"
        elif l.startswith("llama-desc"):
            md += " color: #0000AA"
        elif l == "VQA":
            md += " color: #FF0000"

        md += "\n"

    md += """
```

"""
    return md


def main():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

    document = [make_scatterplot(cursor, None)]

    for collection, c in conn.execute(
        "select collection_name, count(*) as c from images "
        "group by collection_name "
        "order by c desc limit 10",
    ).fetchall():
        document.append(make_scatterplot(cursor, collection, c))

    with open(scatter_file, "w") as f:
        f.write(
            "# Scatter found classes\n\n"
            " - **X-axis***: Ratio of images with men.\n"
            " - **Y-axis***: Ratio of images with women.\n\n"
        )

        f.write(
            '- ![#00FF00](https://placehold.co/15x15/00ff00/00ff00.png) GroundTrut"\n'
        )
        f.write(
            "- ![#999900](https://placehold.co/15x15/999900/999900.png) Dino\n"
        )
        f.write(
            '- ![#0000AA](https://placehold.co/15x15/0000aa/0000aa.png) llama-des"\n'
        )
        f.write(
            "- ![#FF0000](https://placehold.co/15x15/ff0000/ff0000.png) VQA\n"
        )

        f.write("\n".join(document))


if __name__ == "__main__":
    main()
