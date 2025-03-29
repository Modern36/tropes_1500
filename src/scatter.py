import sqlite3

from trope_paths import db_path

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    Collection = "ALL 1500"

    md = f"""```mermaid
quadrantChart
    title Men and women in {Collection}
    x-axis Percent --> Men
    y-axis Percent --> Women
"""

    for l, m, f, c in cursor.execute(
        "select model, "
        "sum(case when label == 'm' then found else 0 end) as m, "
        "sum(case when label == 'w' then found else 0 end) as f, "
        "count(distinct image_id) "
        "from prediction group by model;"
    ):
        if m == f == 0:
            continue
        M = m / c
        F = f / c
        md += f"{l}: [{M}, {F}]"
        if l == "GroundTruth":
            md += " color #00FF00"
        elif l.startswith("Dino"):
            md += " color #999900"
        elif l.startswith("llama-desc"):
            md += " color #0000AA"
        elif l == "VQA":
            md += " color #FF0000"

        md += "\n"


md += """
```

"""
