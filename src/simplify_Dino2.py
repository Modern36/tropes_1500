from itertools import combinations

import pandas as pd
from tqdm import tqdm

from box import Box
from trope_paths import detections


def simplify_dino_boxes():
    pbar = tqdm(total=3000)
    for dino_detection in detections.glob("Dino*[n]_*.tsv"):
        in_name = dino_detection.name
        pbar.desc = in_name
        pbar.update()
        out_name = in_name.replace("_", "2_")
        out_path = dino_detection.parent / out_name
        if out_path.exists():
            continue

        data = pd.read_csv(dino_detection, sep="\t", index_col=None)

        data.sort_values(by="score", ascending=False, inplace=True)
        data.reset_index(drop=True, inplace=True)

        boxes = [
            Box(
                x=row["x0"],
                y=row["y0"],
                x2=row["x1"],
                y2=row["y1"],
                uuid=i,
                l="label",
            )
            for i, row in data.iterrows()
        ]

        for box1, box2 in combinations(boxes, 2):
            if box1.iou(box2) > 0.6:
                box2.keep = False

        for box in boxes:
            if not box.keep:
                data.drop(index=box.uuid, inplace=True)

        data.to_csv(out_path, sep="\t", index=False)


if __name__ == "__main__":
    simplify_dino_boxes()
