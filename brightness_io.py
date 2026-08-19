"""Binary brightness-data I/O shared by the brightness analysis program."""

from __future__ import annotations

import array
import sys
from pathlib import Path


BRIGHTNESS_WIDTH = 4784
BRIGHTNESS_HEIGHT = 3190
FLOAT32_BYTES = 4


def validate_brightness_bin(
    bin_path: str | Path,
    width: int = BRIGHTNESS_WIDTH,
    height: int = BRIGHTNESS_HEIGHT,
) -> Path:
    path = Path(bin_path).expanduser()
    expected_size = width * height * FLOAT32_BYTES
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise ValueError(
            f"亮度文件大小错误：期望 {expected_size} 字节，实际 {actual_size} 字节"
        )
    return path


def convert_brightness_bin_to_txt(
    bin_path: str | Path,
    txt_path: str | Path | None = None,
    width: int = BRIGHTNESS_WIDTH,
    height: int = BRIGHTNESS_HEIGHT,
) -> Path:
    """Convert little-endian float32 data into a height-by-width text matrix."""
    source = validate_brightness_bin(bin_path, width, height)
    destination = Path(txt_path).expanduser() if txt_path else source.with_suffix(".txt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_bytes = width * FLOAT32_BYTES
    with source.open("rb") as binary, destination.open("w", encoding="utf-8", newline="\n") as text:
        for row_index in range(height):
            raw = binary.read(row_bytes)
            if len(raw) != row_bytes:
                raise ValueError(f"亮度文件在第 {row_index + 1} 行提前结束")
            values = array.array("f")
            values.frombytes(raw)
            if sys.byteorder != "little":
                values.byteswap()
            text.write(" ".join(format(value, ".9g") for value in values))
            text.write("\n")
    return destination.resolve()
