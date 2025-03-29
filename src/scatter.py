import sqlite3

from trope_paths import db_path

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    md = """```mermaid
quadrantChart
    title Men and women in material
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
        md += f"{l}: [{M}, {F}]\n"


md += """
```

"""

print(md)
