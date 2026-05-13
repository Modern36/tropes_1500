"""Build static DINO bounding-box viewer site into docs/."""

import csv
import datetime
import html
import io
import json
import shutil
import urllib.request
from pathlib import Path

import yaml
from PIL import Image

from trope_paths import detections, metadata_dir, raw_dir

DOCS = Path(__file__).parents[1] / "docs"
HIRES_CACHE = Path(__file__).parents[1] / "005_hires"
HIRES_URL = "https://mm.dimu.org/image/{id}?dimension=2400x2400"
CITATION_FILE = Path(__file__).parents[1] / "CITATION.cff"

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

YOLO_MODEL = "yolos-pretrained"

PAGE2_IMAGES = [
    {
        "id": "032ymyDgEmA7",
        "label_colors": {
            "person": "#FF0000",
            "chair": "#00FF00",
            "dining table": "#FF66B2",
            "tie": "#FF9933",
            "laptop": "#00FFFF",
        },
    },
    {
        "id": "022wazENVLNx",
        "label_colors": {
            "person": "#FF0000",
            "cell phone": "#FFFFFF",
        },
    },
    {
        "id": "032ykyltssy4",
        "label_colors": {
            "person": "#FF0000",
            "elephant": "#FFFF00",
        },
    },
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


def canonical_image_id(image_id):
    """Return the case-sensitive museum-side image_id from metadata.
    Local filenames are lowercased; the museum API is case-sensitive."""
    meta_path = metadata_dir / f"{image_id}.json"
    with open(meta_path) as f:
        meta = json.load(f)
    return meta["image_id"]


def ensure_hires_image(image_id):
    """Download a higher-resolution version of the image from mm.dimu.org
    into 005_hires/<id>.png. Returns the cached file path. Subsequent
    calls reuse the cache. The local filename uses the lowercased id;
    the URL uses the canonical id from metadata."""
    HIRES_CACHE.mkdir(parents=True, exist_ok=True)
    dst = HIRES_CACHE / f"{image_id}.png"
    if dst.exists():
        return dst
    url = HIRES_URL.format(id=canonical_image_id(image_id))
    req = urllib.request.Request(
        url, headers={"User-Agent": "tropes-1500-build-docs/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        raise RuntimeError(
            f"Failed to download hires image for {image_id} from {url}: {e}"
        ) from e
    img = Image.open(io.BytesIO(data))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dst, format="PNG")
    return dst


def scale_boxes(boxes, scale_x, scale_y):
    """Return a new list of boxes with coordinates rescaled by the given
    per-axis factors. Score and label are passed through unchanged."""
    out = []
    for b in boxes:
        out.append(
            {
                "score": b["score"],
                "label": b["label"],
                "x0": round(b["x0"] * scale_x, 2),
                "y0": round(b["y0"] * scale_y, 2),
                "x1": round(b["x1"] * scale_x, 2),
                "y1": round(b["y1"] * scale_y, 2),
            }
        )
    return out


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
             step="0.05" value="0.25">
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
    <label>Vertical:
      <select id="text_v">
        <option value="top">top</option>
        <option value="center">center</option>
        <option value="bottom">bottom</option>
      </select>
    </label>
    <label>Horizontal:
      <select id="text_h">
        <option value="left">left</option>
        <option value="center">center</option>
        <option value="right">right</option>
      </select>
    </label>
    <label>Placement:
      <select id="text_place">
        <option value="outside">outside</option>
        <option value="inside">inside</option>
      </select>
    </label>
    <label>
      <input type="checkbox" id="fix_overlap">
      Fix overlapping labels
    </label>
  </div>
</div>"""

YOLO_SETTINGS_PANEL_HTML = """\
<div id="settings-panel">
  <div class="settings-row">
    <label>Threshold: <span id="threshold-val">0.25</span>
      <input type="range" id="threshold" min="0" max="1"
             step="0.05" value="0.25">
    </label>
    <label>Thickness: <span id="thickness-val">2</span>
      <input type="range" id="thickness" min="1" max="10"
             step="1" value="2">
    </label>
    <label>Font size: <span id="font_size-val">14</span>
      <input type="range" id="font_size" min="8" max="32"
             step="1" value="14">
    </label>
  </div>
  <div class="settings-row">
    <label>Vertical:
      <select id="text_v">
        <option value="top">top</option>
        <option value="center">center</option>
        <option value="bottom">bottom</option>
      </select>
    </label>
    <label>Horizontal:
      <select id="text_h">
        <option value="left">left</option>
        <option value="center">center</option>
        <option value="right">right</option>
      </select>
    </label>
    <label>Placement:
      <select id="text_place">
        <option value="outside">outside</option>
        <option value="inside">inside</option>
      </select>
    </label>
    <label>
      <input type="checkbox" id="fix_overlap">
      Fix overlapping labels
    </label>
  </div>
  <div class="settings-row" id="label-colors-row"></div>
</div>"""


def header_nav_html(active, depth):
    """Return the three-tab header nav. depth=0 for root pages, 1 for
    image pages (in subdirectories)."""
    prefix = "../" if depth == 1 else ""
    dino_class = ' class="active"' if active == "dino" else ""
    yolo_class = ' class="active"' if active == "yolo" else ""
    cite_class = ' class="active"' if active == "citation" else ""
    return (
        '<nav class="page-nav">'
        f'<a href="{prefix}index.html"{dino_class}>DINO (Man/Woman)</a>'
        f'<a href="{prefix}objects.html"{yolo_class}>YOLO (Objects)</a>'
        f'<a href="{prefix}citation.html"{cite_class}>Citation</a>'
        "</nav>"
    )


def label_colors_attr(label_colors):
    """Serialize a label_colors dict as a safe HTML attribute value."""
    return html.escape(json.dumps(label_colors), quote=True)


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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
</head>
<body data-page="dino">
  {header_nav_html("dino", 0)}
  <h1>DINO Bounding Box Viewer</h1>
{SETTINGS_PANEL_HTML}
  <div class="download-bar">
    <button id="download-all" class="btn-download">Download all images (.zip)</button>
  </div>
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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
</head>
<body data-page="dino">
  {header_nav_html("dino", 1)}
  <div class="image-page-nav">
    <a id="back-link" href="../index.html">&#8592; Back to gallery</a>
    <button id="use-for-all">Use these settings for all images</button>
    <button id="download-image" class="btn-download"
            data-image-id="{img['id']}">Download image (.zip)</button>
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


def objects_gallery_html(image_data):
    """Generate the YOLO objects gallery page."""
    cards = []
    for img in image_data:
        colors_attr = label_colors_attr(img["label_colors"])
        card = f"""\
    <a class="card" href="objects/{img['id']}.html"
       data-image-id="{img['id']}"
       data-width="{img['width']}"
       data-height="{img['height']}"
       data-label-colors="{colors_attr}">
      <div class="image-wrap">
        <img src="images_hires/{img['id']}.png"
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
  <title>YOLO Object Detection Viewer</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
</head>
<body data-page="objects">
  {header_nav_html("yolo", 0)}
  <h1>YOLO Object Detection Viewer</h1>
{YOLO_SETTINGS_PANEL_HTML}
  <div class="download-bar">
    <button id="download-all" class="btn-download">Download all images (.zip)</button>
  </div>
  <div id="gallery">
{cards_html}
  </div>
  <script src="app.js"></script>
</body>
</html>
"""


def yolo_image_page_html(img):
    """Generate a per-image HTML page for the YOLO gallery."""
    colors_attr = label_colors_attr(img["label_colors"])
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{img['id']} — YOLO Object Detection Viewer</title>
  <link rel="stylesheet" href="../style.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
</head>
<body data-page="objects">
  {header_nav_html("yolo", 1)}
  <div class="image-page-nav">
    <a id="back-link" href="../objects.html">&#8592; Back to gallery</a>
    <button id="use-for-all">Use these settings for all images</button>
    <button id="download-image" class="btn-download"
            data-image-id="{img['id']}">Download image (.zip)</button>
  </div>
  <h1>{img['id']}</h1>
{YOLO_SETTINGS_PANEL_HTML}
  <div class="single-image-wrap"
       data-image-id="{img['id']}"
       data-width="{img['width']}"
       data-height="{img['height']}"
       data-label-colors="{colors_attr}">
    <img src="../images_hires/{img['id']}.png"
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
# Citation
# ------------------------------------------------------------------


def load_citation():
    """Read CITATION.cff into a dict (single source of truth for the
    citation page)."""
    with open(CITATION_FILE) as f:
        return yaml.safe_load(f)


def citation_date(citation):
    """Return the date-released field as a datetime.date, regardless of
    whether PyYAML parsed it as a date or as a string."""
    d = citation["date-released"]
    if isinstance(d, datetime.date):
        return d
    return datetime.datetime.strptime(d, "%Y-%m-%d").date()


def format_authors_apa(authors):
    """Render authors as 'Last, F., Last, F., & Last, F.' (APA-ish)."""
    parts = []
    for a in authors:
        initial = a["given-names"][:1] + "."
        parts.append(f"{a['family-names']}, {initial}")
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def make_bibtex(citation):
    """Generate a BibTeX entry from the CFF data."""
    date = citation_date(citation)
    month_abbrev = date.strftime("%b").lower()
    last = citation["authors"][0]["family-names"].lower()
    doi_suffix = str(citation["doi"]).rsplit(".", 1)[-1]
    key = f"{last}_{date.year}_{doi_suffix}"
    indent = " " * 18
    authors_block = (" and\n" + indent).join(
        f"{a['family-names']}, {a['given-names']}" for a in citation["authors"]
    )
    publisher = citation.get("publisher", {}).get("name", "Zenodo")
    return (
        f"@dataset{{{key},\n"
        f"  author       = {{{authors_block}}},\n"
        f"  title        = {{{citation['title']}}},\n"
        f"  month        = {month_abbrev},\n"
        f"  year         = {date.year},\n"
        f"  publisher    = {{{publisher}}},\n"
        f"  version      = {{{citation['version']}}},\n"
        f"  doi          = {{{citation['doi']}}},\n"
        f"  url          = {{{citation['url']}}},\n"
        f"}}"
    )


def citation_html(citation):
    """Render docs/citation.html from the CFF data."""
    date = citation_date(citation)
    authors_apa = format_authors_apa(citation["authors"])
    publisher = citation.get("publisher", {}).get("name", "Zenodo")
    doi = citation["doi"]
    bibtex = make_bibtex(citation)
    cite_line = (
        f"{authors_apa} ({date.year}). "
        f"<em>{html.escape(citation['title'])}</em> "
        f"(Version {html.escape(citation['version'])}) [Dataset]. "
        f"{html.escape(publisher)}. "
        f'<a href="{html.escape(citation["url"], quote=True)}">'
        f"{html.escape(citation['url'])}</a>"
    )
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citation — {html.escape(citation['title'])}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body data-page="citation">
  {header_nav_html("citation", 0)}
  <h1>Cite this dataset</h1>
  <div class="citation-content">
    <p>{html.escape(citation['message'])}</p>
    <p class="cite-line">{cite_line}</p>
    <h2>BibTeX</h2>
    <pre><code>{html.escape(bibtex)}</code></pre>
    <h2>DOI</h2>
    <p><a href="https://doi.org/{html.escape(str(doi), quote=True)}">{html.escape(str(doi))}</a></p>
  </div>
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
    for d in [
        DOCS,
        DOCS / "image",
        DOCS / "images",
        DOCS / "data",
        DOCS / "objects",
        DOCS / "images_hires",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # ---- Page 1: DINO gallery ----

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
                f.write("\n")
            json_count += 1
    print(f"Generated {json_count} DINO detection JSON files")

    # Generate HTML pages
    (DOCS / "index.html").write_text(gallery_html(image_data))
    for img in image_data:
        (DOCS / "image" / f"{img['id']}.html").write_text(image_page_html(img))
    print(f"Generated DINO gallery + {len(image_data)} image pages")

    # ---- Page 2: YOLO objects gallery (higher-res images) ----

    page2_data = []
    for entry in PAGE2_IMAGES:
        raw_w, raw_h = get_image_dimensions(entry["id"])
        hires_path = ensure_hires_image(entry["id"])
        with Image.open(hires_path) as hires_img:
            hires_w, hires_h = hires_img.size
        sx = hires_w / raw_w
        sy = hires_h / raw_h
        if abs(sx - sy) > 0.005:
            raise RuntimeError(
                f"Aspect-ratio mismatch for {entry['id']}: "
                f"raw {raw_w}x{raw_h} vs hires {hires_w}x{hires_h} "
                f"(sx={sx:.4f}, sy={sy:.4f})"
            )
        print(
            f"  {entry['id']}: {raw_w}x{raw_h} -> {hires_w}x{hires_h} "
            f"(x{sx:.2f})"
        )
        page2_data.append(
            {
                "id": entry["id"],
                "width": hires_w,
                "height": hires_h,
                "label_colors": entry["label_colors"],
                "scale_x": sx,
                "scale_y": sy,
            }
        )
        shutil.copy2(hires_path, DOCS / "images_hires" / f"{entry['id']}.png")

    # YOLO detection JSONs with rescaled box coordinates
    for img in page2_data:
        boxes = scale_boxes(
            load_tsv_boxes(YOLO_MODEL, img["id"]),
            img["scale_x"],
            img["scale_y"],
        )
        data = {
            "image_id": img["id"],
            "model": YOLO_MODEL,
            "width": img["width"],
            "height": img["height"],
            "boxes": boxes,
        }
        out_path = DOCS / "data" / f"{YOLO_MODEL}_{img['id']}.json"
        with open(out_path, "w") as f:
            json.dump(data, f)
            f.write("\n")
    print(f"Generated {len(page2_data)} YOLO detection JSON files")

    (DOCS / "objects.html").write_text(objects_gallery_html(page2_data))
    for img in page2_data:
        (DOCS / "objects" / f"{img['id']}.html").write_text(
            yolo_image_page_html(img)
        )
    print(f"Generated YOLO gallery + {len(page2_data)} image pages")

    # ---- Citation page ----

    citation = load_citation()
    (DOCS / "citation.html").write_text(citation_html(citation))
    print("Generated citation page")

    # Copy static assets
    for asset in ["app.js", "style.css"]:
        shutil.copy2(ASSETS_DIR / asset, DOCS / asset)
    print("Copied static assets")

    # Write .nojekyll
    (DOCS / ".nojekyll").write_text("")
    print("Done — docs/ ready")


if __name__ == "__main__":
    build_docs()
