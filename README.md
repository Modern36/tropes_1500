# Tropes 1500

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

> Citation information will be added here once a DOI has been assigned.

## License

> License information will be added here.
