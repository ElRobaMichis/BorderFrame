"""Utility functions for BorderFrame."""

from typing import Optional, Tuple

from PIL import Image, ImageOps
from PyQt5.QtGui import QPixmap, QImage

try:  # Pillow < 10
    from PIL.ImageQt import ImageQt  # type: ignore
    _HAS_IMAGEQT = True
except Exception:  # pragma: no cover - fallback for newer Pillow versions
    ImageQt = None  # type: ignore
    _HAS_IMAGEQT = False


def calculate_dimensions(img_width: int, img_height: int, border_size: int, aspect_ratio: Optional[Tuple[int, int]]):
    """Calculate new dimensions for adding a border while respecting an optional aspect ratio."""
    if aspect_ratio is None:
        new_width = img_width + (border_size * 2)
        new_height = img_height + (border_size * 2)
    else:
        target_ratio = aspect_ratio[0] / aspect_ratio[1]
        min_width = img_width + (border_size * 2)
        min_height = img_height + (border_size * 2)
        current_ratio = min_width / min_height

        if current_ratio > target_ratio:
            new_width = min_width
            new_height = int(new_width / target_ratio)
            new_height = max(new_height, min_height)
        else:
            new_height = min_height
            new_width = int(new_height * target_ratio)
            new_width = max(new_width, min_width)

    return new_width, new_height


def load_pixmap(path: str) -> QPixmap:
    """Load image as QPixmap applying EXIF orientation if present."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        rgba = img.convert("RGBA")
        if _HAS_IMAGEQT:
            qimage = ImageQt(rgba)  # type: ignore[misc]
        else:  # pragma: no cover - fallback when ImageQt is unavailable
            data = rgba.tobytes("raw", "RGBA")
            qimage = QImage(data, rgba.width, rgba.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)
