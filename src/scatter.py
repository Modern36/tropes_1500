import sqlite3

import pandas as pd
from sklearn.metrics import classification_report

from trope_paths import db_path, scatter_data_file, scatter_file

one_char = {
    "GroundTruth": "GT",
    "VQA": "V",
    "DinoManWoman": "M",
    "DinoWomanMan": "W",
    "DinoManWoman2": "M2",
    "DinoWomanMan2": "W2",
    "llama-desc": "L",
}

metric_to_symbol = {"f1-score": "f", "precision": "p", "recall": "r"}


def make_scatterplot(cursor, Collection_in=None, c=1500):
    if Collection_in is None:
        Collection = "ALL "
    else:
        Collection = Collection_in

    md = f"""

```mermaid
quadrantChart
    title Men and women in {Collection_in} {c}
    x-axis Percent --> Men
    y-axis Percent --> Women
"""

    for l, m, f, c in get_label_counts(cursor, Collection_in):
        if m == f == 0:
            continue
        if "2" in l:
            continue
        M = m / c
        F = f / c
        md += f"    {one_char[l]}%: [{M}, {F}]"
        md += add_color(l)

        md += "\n"

    # Calculate and add metrics.

    for model, m_c_r, w_c_r in get_classification_reports(
        cursor=cursor, Collection=Collection
    ):
        for metric in ["f1-score", "precision", "recall"]:
            x = m_c_r["1"][metric]
            if x == 1.0:
                x = 0.9999
            y = w_c_r["1"][metric]
            if y == 1.0:
                y = 0.9999
            char = one_char[model].upper()

            metric_symbol = metric_to_symbol[metric]
            color = add_color(model)

            assert y != 1

            md += f"    {char}{metric_symbol}: [{x}, {y}] {color} \n"

    md += """
```

"""
    return md


def get_classification_reports(*, cursor, Collection):
    GT = image_level_output_for_model(cursor, collection=Collection)

    m_gt, w_gt = GT

    for model, *_ in cursor.execute(
        """
        SELECT model
        FROM prediction
        where model != 'GroundTruth'
        and label in ("m", "w")
        group by model
        ORDER BY model desc
        """
    ).fetchall():
        if "2" in model:
            continue
        m_pred, w_pred = image_level_output_for_model(
            cursor, collection=Collection, model=model
        )

        assert len(m_pred) == len(w_pred)
        assert len(m_gt) == len(w_gt)

        m_c_r = classification_report(
            y_true=m_gt,
            y_pred=m_pred,
        )
        w_c_r = classification_report(
            y_true=w_gt,
            y_pred=w_pred,
            output_dict=True,
        )

        yield model, m_c_r, w_c_r


def get_label_counts(cursor, collection):
    query = make_counts_query(collection)
    return cursor.execute(query)


def make_counts_query(Collection):
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
    return query


def image_level_output_for_model(
    cursor,
    collection,
    model="GroundTruth",
):
    query = """
        SELECT found
        FROM prediction """
    if collection.strip() != "ALL":
        query += (
            "join images on prediction.image_id == images.image_id "
            f"where collection_name = '{collection}' and "
        )
    else:
        query += "Where "

    query += """
         model == :model and label == :label
        group by prediction.image_id
        ORDER BY prediction.image_id desc
        """

    m = cursor.execute(query, {"model": model, "label": "m"}).fetchall()
    w = cursor.execute(query, {"model": model, "label": "w"}).fetchall()

    return m, w


def add_color(l):
    if l == "GroundTruth":
        return " color: #00FF00"
    elif l.startswith("Dino"):
        return " color: #999900"
    elif l.startswith("llama-desc"):
        return " color: #0000AA"
    elif l == "VQA":
        return " color: #FF0000"


def scatter_to_markdown():
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
            " - **X-axis**: Ratio of images with men.\n"
            " - **Y-axis**: Ratio of images with women.\n\n"
        )

        f.write(
            """
| Color | Model | | Symbol | Metric |
| ---   |:--- | --- | ---: |:---    |
|![#00FF00](https://placehold.co/15x15/00ff00/00ff00.png)| (GT) GroundTruth| | % | Ratio of images with object |
|![#999900](https://placehold.co/15x15/999900/999900.png)| (W/M) Dino| | f | F1-score |
|![#0000AA](https://placehold.co/15x15/0000aa/0000aa.png)| (L) llama-desc| | p | Precision |
|![#FF0000](https://placehold.co/15x15/ff0000/ff0000.png)| (V) VQA| | r | Recall |
"""
        )

        f.write("\n".join(document))


def scatter_data_for_file():
    data = []

    with sqlite3.connect(db_path, uri=True) as conn:
        Collection = "ALL"
        for model, m, f, c in get_label_counts(
            cursor=conn.cursor(),
            collection=None,
        ):
            assert c == 1500
            data.append(("count", model, m, f))
            data.append(("share", model, m / c, f / c))

    for model, m_c_r, w_c_r in get_classification_reports(
        cursor=conn.cursor(),
        Collection=Collection,
    ):
        for metric in ["f1-score", "precision", "recall"]:
            x = m_c_r["1"][metric]
            y = w_c_r["1"][metric]

            data.append((metric, model, x, y))
    return data


if __name__ == "__main__":
    scatter_to_markdown()

    data = scatter_data_for_file()
    df = pd.DataFrame(sorted(data))
    df.columns = ["metric", "model", "men", "women"]
    df.to_csv(scatter_data_file, index=False)
