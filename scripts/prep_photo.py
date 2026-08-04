"""
prep_photo.py

Takes a raw photo and produces a clean, high-contrast grayscale image
ready for ASCII conversion:
  1. Remove background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so a flatly-lit face gets real
     highlights/shadows.
  3. Composite onto pure white so background maps to the blank end
     of the ASCII ramp.

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    source-prepped.png  (grayscale, ready for make_ascii_svg.py)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str = None) -> str:
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "-prepped.png")

    # 1. Remove background -> RGBA with transparent bg
    with open(input_path, "rb") as f:
        cutout = remove(f.read())

    rgba = Image.open(__import__("io").BytesIO(cutout)).convert("RGBA")

    # 2. Composite onto pure white
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. CLAHE contrast boost (operate in grayscale)
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    out_img = Image.fromarray(enhanced)
    out_img.save(output_path)
    print(f"Wrote {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>")
        sys.exit(1)
    prep_photo(sys.argv[1])
