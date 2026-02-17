# Tropes 1500

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18672094.svg)](https://doi.org/10.5281/zenodo.18672094)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

Gender bias in object detection models applied to 1,500 annotated 1930s Swedish photographs from [Digitalt Museum](https://digitaltmuseum.se/). The project compares how different models detect men versus women, generating classification metrics and a markdown-based browsing interface for the results.

## Models

| Model | Type | Labels | Notes |
|-------|------|--------|-------|
| DinoManWoman | Grounding DINO v1 | man, woman, person | Label order: Man first |
| DinoWomanMan | Grounding DINO v1 | woman, man, person | Label order: Woman first |
| DinoManWoman2 | Grounding DINO v2 | man, woman, person | Label order: Man first |
| DinoWomanMan2 | Grounding DINO v2 | woman, man, person | Label order: Woman first |
| YOLO_50 | YOLO | person | Confidence threshold 50% |
| YOLO_75 | YOLO | person | Confidence threshold 75% |
| YOLO_90 | YOLO | person | Confidence threshold 90% |
| VQA | ViLT-VQA | man, woman, person | Visual question answering with 7 questions per gender |
| llama-desc | Llama Vision + Mistral | man, woman, person | Two-stage: Llama describes the image, Mistral extracts binary labels |

Label order matters for Grounding DINO -- the model produces different results depending on whether "Man" or "Woman" appears first in the prompt.

## Browsing the results

The `browser/` directory contains a markdown-based interface for exploring model outputs:

- **Per-model pages** (`browser/<Model>/`) -- classification reports and per-collection breakdowns
- **Scatter plots** (`browser/scatter.md`) -- Mermaid quadrant charts comparing F1, precision, and recall across models and genders
- **Gathering** (`browser/gathering/`) -- images grouped by cross-model accuracy (AllGood, AllBad, Good_X, Bad_X)

## Data

| File | Description |
|------|-------------|
| `data.csv` | Ground truth and model predictions for all 1,500 images |
| `scatter_data.csv` | Pre-computed metrics used by the scatter plots |
| `metadata_jsons/` | One JSON per image with museum metadata |
| `statistics/` | Classification reports and manual correction files |

## Source images

The 1,500 photographs originate from [Digitalt Museum](https://digitaltmuseum.se/) and are not included in this repository. The `000_raw/` directory is expected to contain the images locally; model output images with bounding boxes are in `010_model_output/`.

## Related repositories

- [m36_utils](https://github.com/Modern36/m36_utils) -- model wrappers for Grounding DINO, YOLO, and VQA
- [m36_tropes](https://github.com/Modern36/visual_tropes) -- shared tropes utilities

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions, commands, code style, and architecture details.

## Citation

If you use this data, please cite this repository and [Digitalt Museum](https://digitaltmuseum.se/) as the source of the photographs:

```bibtex
@dataset{johansson_2026_18672094,
  author       = {Johansson, Mathias and
                  Norén, Fredrik and
                  Aspenskog, Robert and
                  Eriksson, Maria},
  title        = {Visual Tropes 1500},
  month        = feb,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {2026-02-17},
  doi          = {10.5281/zenodo.18672094},
  url          = {https://doi.org/10.5281/zenodo.18672094},
}

@misc{digitaltmuseum,
  title        = {Digitalt Museum},
  author       = {{KulturIT}},
  url          = {https://digitaltmuseum.se/},
}
```

## License

This project is licensed under [CC-BY-NC-4.0](LICENSE).

## Additional references

Depending on which part of the data you use, please also consider citing the underlying models and datasets. Full bibtex entries are in [`references.bib`](references.bib).

| If you use | Please cite |
|------------|-------------|
| Grounding DINO v1 results (DinoManWoman, DinoWomanMan) | Liu et al., 2024 — Grounding DINO (ECCV 2024) |
| Grounding DINO v2 results (DinoManWoman2, DinoWomanMan2) | Ren et al., 2024 — Grounding DINO 1.5 |
| YOLO results (YOLO_50, YOLO_75, YOLO_90) | Fang et al., 2021 — YOLOS (NeurIPS 2021) |
| VQA results | Kim et al., 2021 — ViLT (ICML 2021) |
| llama-desc results | Dubey et al., 2024 — Llama 3; Mistral AI, 2025 — Mistral Small 3.1 |
| Ground truth annotations | Nakayama et al., 2018 — doccano |
| Classification metrics | Pedregosa et al., 2011 — scikit-learn |
| Any model trained on COCO | Lin et al., 2014 — Microsoft COCO (ECCV 2014) |
| Any model pre-trained on ImageNet | Deng et al., 2009 — ImageNet (CVPR 2009) |
