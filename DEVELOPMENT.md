# Development

Technical setup and workflow for contributing to Tropes 1500.

## Prerequisites

- Python 3.10+
- Access to the [Modern36](https://github.com/Modern36) GitHub organisation (for `m36_utils` and `m36_tropes`)
- [ollama](https://ollama.com/) installed locally (for LLM-based inference)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Commands

```bash
# Run all tests
pytest

# Run a single test
pytest tests/count_files_test.py::test_count_DinoManWoman_th25

# Rebuild the SQLite database from raw data (also recalculates groupings)
python src/build_db.py

# Regenerate scatter plot visualization
python src/scatter.py

# Regenerate the markdown browser
python src/build_browsing.py
```

## Code style

- **Formatter:** [Black](https://black.readthedocs.io/), 79-character line length
- **Import sorting:** [isort](https://pycqa.github.io/isort/) with Black profile
- **Pre-commit hooks:** isort, Black, trailing whitespace, pytest (all tests must pass), and scatter plot regeneration run before every commit

## Architecture

### Pipeline

```
000_raw/ (images) --> model inference --> 010_model_output/ + 999_detect_data/
    --> build_db.py      --> db.sqlite3
    --> scatter.py       --> scatter_data.csv + browser/scatter.md
    --> build_browsing.py --> browser/ (markdown pages)
    --> browser_group_best_worst.py --> browser/gathering/
```

### Key source files (`src/`)

| File | Purpose |
|------|---------|
| `trope_paths.py` | Central path definitions and `model_to_subdir` mapping. All other modules import paths from here. |
| `build_db.py` | Builds `db.sqlite3` from scratch: loads metadata JSONs, ground truth from `data.csv`, model predictions from TSV detection files, llama descriptions with corrections. |
| `build_browsing.py` | Generates the `browser/` markdown tree from database queries. Produces per-model, per-collection pages with classification reports. |
| `scatter.py` | Computes F1/precision/recall metrics and generates Mermaid quadrant charts in `browser/scatter.md`. |
| `browser_group_best_worst.py` | Categorises images by cross-model accuracy (AllGood, AllBad, Good_X, Bad_X) into the `gathering` DB table. |
| `box.py` | Bounding box class with IoU calculation, used by `simplify_Dino2.py`. |
| `prepare_data.py` | Wraps model inference (uses `m36_utils` classes `GrounDino`, `YolosBase`). |

### Data files

| File/directory | Description |
|----------------|-------------|
| `data.csv` | Ground truth + model predictions for all 1,500 images. |
| `db.sqlite3` | SQLite database (tables: `images`, `prediction`, `yolo`, `gathering`). Not checked in; rebuilt with `build_db.py`. |
| `metadata_jsons/` | One JSON per image with museum metadata. |
| `statistics/Llama-binary_correction.csv` | Manual overrides for llama-desc model output. |

### Key concepts

- **Label order matters:** Grounding DINO produces different results depending on label order ("Man, Woman" vs "Woman, Man"), tracked as separate models (`DinoManWoman` vs `DinoWomanMan`).
- **Labels:** `m` = man, `w` = woman, `p` = person. Person is always true if either man or woman is true.
- **YOLO thresholds:** 50/75/90 confidence thresholds produce different model variants. YOLO detects "person" only (no gender).
- **Image path resolution:** `resolve_image_path()` in `trope_paths.py` falls back through YOLO thresholds and then to raw images if annotated versions don't exist.

## Dependencies

| Package | Source | Purpose |
|---------|--------|---------|
| `m36_utils` | [Modern36/m36_utils](https://github.com/Modern36/m36_utils) | Model wrappers (`GrounDino`, `YolosBase`) |
| `m36_tropes` | [Modern36/visual_tropes](https://github.com/Modern36/visual_tropes) | Shared tropes utilities |
| `pandas` | PyPI | Data manipulation |
| `scikit-learn` | PyPI | Classification reports |
| `ollama` | PyPI | Local LLM inference |
| `tqdm` | PyPI | Progress bars |
