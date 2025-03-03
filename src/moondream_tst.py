"""
Download model: https://huggingface.co/vikhyatk/moondream2/resolve/9dddae84d54db4ac56fe37817aeaeb502ed083e2/moondream-2b-int8.mf.gz?download=true
"""

import moondream as md
from PIL import Image
from trope_paths import output_dir

# Initialize with local model path. Can also read .mf.gz files, but we recommend decompressing
# up-front to avoid decompression overhead every time the model is initialized.
model = md.vl(
    model=str(output_dir / "moondreammodel" / "moondream-2b-int8.mf")
)

# Load and process image
image = Image.open(output_dir / "DinoWomanMan_th25/022yi14dr7qw.png")
encoded_image = model.encode_image(image)

# Generate caption
caption = model.caption(encoded_image)["caption"]
print("Caption:", caption)

# Ask questions
answer = model.query(encoded_image, "What's in this image?")["answer"]
print("Answer:", answer)
