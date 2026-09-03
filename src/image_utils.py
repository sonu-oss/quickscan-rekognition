"""
src/image_utils.py

Draws Rekognition's bounding boxes onto the original image using Pillow.

Rekognition returns bounding boxes as RATIOS (0.0-1.0) of image width/height,
not pixel coordinates - e.g. Left=0.25 means "25% in from the left edge".
This file converts those ratios into actual pixel coordinates for the
specific image being annotated.
"""

import zlib

from PIL import Image, ImageDraw, ImageFont

# A small, fixed palette so repeated labels get a consistent, readable color
# and text stays legible against most backgrounds.
BOX_COLORS = [
    "#5EEAD4", "#F2A64B", "#F2765A", "#8B9CF2",
    "#7CE38B", "#F2E15E", "#E27CF2", "#4BC3F2",
]


def _color_for_label(label: str) -> str:
    """Deterministically picks a color per label name, so the same item
    (e.g. every "Apple") is always outlined in the same color."""
    # Python hashes are randomized for each process; CRC32 keeps a label's
    # colour stable across app restarts and presentation screenshots.
    return BOX_COLORS[zlib.crc32(label.encode("utf-8")) % len(BOX_COLORS)]


def _load_font(size: int = 18):
    # Falls back to PIL's built-in bitmap font if no TTF font is available
    # on the system - keeps this working in minimal/container environments.
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_bounding_boxes(image: Image.Image, detections: list[dict]) -> Image.Image:
    """
    Parameters
    ----------
    image : the original PIL image (RGB)
    detections : output of rekognition_client.flatten_instances(), i.e. a
                 list of {"label", "confidence", "box", "parents"} dicts

    Returns
    -------
    A NEW PIL image with boxes and labels drawn on it (the original image
    passed in is left untouched, so the UI can still show "before").
    """
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)
    img_w, img_h = annotated.size
    font = _load_font(max(14, img_w // 60))

    boxed_count = 0
    for det in detections:
        box = det["box"]
        if box is None:
            continue  # scene-level label, nothing to draw

        color = _color_for_label(det["label"])

        left = box["Left"] * img_w
        top = box["Top"] * img_h
        width = box["Width"] * img_w
        height = box["Height"] * img_h
        right, bottom = left + width, top + height

        line_width = max(2, img_w // 400)
        draw.rectangle([left, top, right, bottom], outline=color, width=line_width)

        caption = f"{det['label']} {det['confidence']:.0f}%"
        text_bbox = draw.textbbox((0, 0), caption, font=font)
        text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        pad = 4

        label_top = max(0, top - text_h - 2 * pad)
        draw.rectangle(
            [left, label_top, left + text_w + 2 * pad, label_top + text_h + 2 * pad],
            fill=color,
        )
        draw.text((left + pad, label_top + pad), caption, fill="#0D1117", font=font)

        boxed_count += 1

    return annotated
