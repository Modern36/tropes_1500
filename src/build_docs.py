"""Build static DINO bounding-box viewer site into docs/."""

import csv
import json
import shutil
from pathlib import Path

from PIL import Image

from trope_paths import detections, raw_dir

DOCS = Path(__file__).parents[1] / "docs"

IMAGE_IDS = [
    "032ykyltssy4",
    "013Ajtq1HmyS",
    "032s93sf4BrP",
    "02347SnUJTXC",
    "032sB2qaj2UK",
    "022wazENVLNx",
    "022ykz8eCidZ",
    "022wY1AVY1GL",
    "032wazZx6WPq",
    "012uN2AeVDLe",
    "022ykzMkkhbw",
    "032ykz8ZkkQW",
    "042s8YsxtqVz",
]

DINO_MODELS = [
    "DinoManWoman",
    "DinoManWoman2",
    "DinoWomanMan",
    "DinoWomanMan2",
]

ASSETS_DIR = Path(__file__).parent / "docs_assets"


# ------------------------------------------------------------------
# Data helpers
# ------------------------------------------------------------------


def get_image_dimensions(image_id):
    """Return (width, height) for a raw image."""
    img = Image.open(raw_dir / f"{image_id}.png")
    return img.size


def load_tsv_boxes(model, image_id):
    """Load bounding boxes from a TSV detection file."""
    tsv_path = detections / f"{model}_{image_id}.tsv"
    boxes = []
    if not tsv_path.exists():
        return boxes
    with open(tsv_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar='"')
        for row in reader:
            boxes.append(
                {
                    "score": round(float(row["score"]), 4),
                    "label": row["label"],
                    "x0": round(float(row["x0"]), 2),
                    "y0": round(float(row["y0"]), 2),
                    "x1": round(float(row["x1"]), 2),
                    "y1": round(float(row["y1"]), 2),
                }
            )
    return boxes


# ------------------------------------------------------------------
# HTML generation
# ------------------------------------------------------------------

SETTINGS_PANEL_HTML = """\
<div id="settings-panel">
  <div class="settings-row">
    <label>Model:
      <select id="model">
        <option value="DinoManWoman">DinoManWoman</option>
        <option value="DinoManWoman2">DinoManWoman2</option>
        <option value="DinoWomanMan">DinoWomanMan</option>
        <option value="DinoWomanMan2">DinoWomanMan2</option>
      </select>
    </label>
    <label>Threshold: <span id="threshold-val">0.25</span>
      <input type="range" id="threshold" min="0" max="1"
             step="0.01" value="0.25">
    </label>
  </div>
  <div class="settings-row">
    <label>Man color:
      <input type="color" id="man_color" value="#0000ff">
    </label>
    <label>Woman color:
      <input type="color" id="woman_color" value="#ff0000">
    </label>
    <label>Thickness: <span id="thickness-val">2</span>
      <input type="range" id="thickness" min="1" max="10"
             step="1" value="2">
    </label>
    <label>Font size: <span id="font_size-val">14</span>
      <input type="range" id="font_size" min="8" max="32"
             step="1" value="14">
    </label>
    <label>Text position:
      <select id="text_pos">
        <option value="top-left">top-left</option>
        <option value="top-right">top-right</option>
        <option value="bottom-left">bottom-left</option>
        <option value="bottom-right">bottom-right</option>
      </select>
    </label>
  </div>
</div>"""


def gallery_html(image_data):
    """Generate the gallery index.html page."""
    cards = []
    for img in image_data:
        card = f"""\
    <a class="card" href="image/{img['id']}.html"
       data-image-id="{img['id']}"
       data-width="{img['width']}"
       data-height="{img['height']}">
      <div class="image-wrap">
        <img src="images/{img['id']}.png"
             alt="{img['id']}"
             width="{img['width']}"
             height="{img['height']}">
        <svg class="overlay"
             viewBox="0 0 {img['width']} {img['height']}"
             preserveAspectRatio="xMidYMid meet"></svg>
      </div>
      <span class="card-label">{img['id']}</span>
    </a>"""
        cards.append(card)

    cards_html = "\n".join(cards)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DINO Bounding Box Viewer</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>DINO Bounding Box Viewer</h1>
{SETTINGS_PANEL_HTML}
  <div id="gallery">
{cards_html}
  </div>
  <script src="app.js"></script>
</body>
</html>
"""


def image_page_html(img):
    """Generate a per-image HTML page."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{img['id']} — DINO Bounding Box Viewer</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <div class="image-page-nav">
    <a id="back-link" href="../index.html">&#8592; Back to gallery</a>
    <button id="use-for-all">Use these settings for all images</button>
  </div>
  <h1>{img['id']}</h1>
{SETTINGS_PANEL_HTML}
  <div class="single-image-wrap"
       data-image-id="{img['id']}"
       data-width="{img['width']}"
       data-height="{img['height']}">
    <img src="../images/{img['id']}.png"
         alt="{img['id']}"
         width="{img['width']}"
         height="{img['height']}">
    <svg class="overlay"
         viewBox="0 0 {img['width']} {img['height']}"
         preserveAspectRatio="xMidYMid meet"></svg>
  </div>
  <h2>Detections</h2>
  <table id="detections-table">
    <thead>
      <tr>
        <th>Label</th><th>Score</th><th>Visible</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
  <script src="../app.js"></script>
</body>
</html>
"""


# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------


def build_docs():
    """Build the complete docs/ site."""
    # Clean and create directories
    if DOCS.exists():
        shutil.rmtree(DOCS)
    for d in [DOCS, DOCS / "image", DOCS / "images", DOCS / "data"]:
        d.mkdir(parents=True, exist_ok=True)

    # Collect image data
    image_data = []
    for image_id in IMAGE_IDS:
        w, h = get_image_dimensions(image_id)
        image_data.append({"id": image_id, "width": w, "height": h})

    # Copy raw images
    for img in image_data:
        src = raw_dir / f"{img['id']}.png"
        dst = DOCS / "images" / f"{img['id']}.png"
        shutil.copy2(src, dst)
    print(f"Copied {len(image_data)} images")

    # Convert TSV detection data to JSON
    json_count = 0
    for model in DINO_MODELS:
        for img in image_data:
            boxes = load_tsv_boxes(model, img["id"])
            data = {
                "image_id": img["id"],
                "model": model,
                "width": img["width"],
                "height": img["height"],
                "boxes": boxes,
            }
            out_path = DOCS / "data" / f"{model}_{img['id']}.json"
            with open(out_path, "w") as f:
                json.dump(data, f)
            json_count += 1
    print(f"Generated {json_count} detection JSON files")

    # Generate HTML pages
    (DOCS / "index.html").write_text(gallery_html(image_data))
    for img in image_data:
        (DOCS / "image" / f"{img['id']}.html").write_text(image_page_html(img))
    print(f"Generated gallery + {len(image_data)} image pages")

    # Copy static assets
    for asset in ["app.js", "style.css"]:
        shutil.copy2(ASSETS_DIR / asset, DOCS / asset)
    print("Copied static assets")

    # Write .nojekyll
    (DOCS / ".nojekyll").write_text("")
    print("Done — docs/ ready")


if __name__ == "__main__":
    build_docs()
