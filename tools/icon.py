#!/usr/bin/env python3
"""Draws icons/vastcompressed.png (256x256): the three bands' frames one inside another, around a packed core."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_content import BANDS, png  # noqa: E402

SIZE, SCALE = 16, 16


def main():
    px = [[(0, 0, 0, 0)] * SIZE for _ in range(SIZE)]

    def ring(inset, dark, light):
        mid = tuple((d + l) // 2 for d, l in zip(dark, light))
        lo, hi = inset, SIZE - 1 - inset
        for i in range(lo, hi + 1):
            px[lo][i] = px[hi][i] = px[i][lo] = px[i][hi] = (*dark, 255)
        for i in range(lo + 1, hi):
            px[lo + 1][i] = px[i][lo + 1] = (*light, 255)
            px[hi - 1][i] = px[i][hi - 1] = (*mid, 255)

    for inset, (dark, light) in zip((0, 2, 4), reversed(BANDS)):
        ring(inset, dark, light)
    # The core: a packed stone of its own, speckled.
    for y in range(6, 10):
        for x in range(6, 10):
            v = 0x7C + (0x18 if (x + y) % 3 == 0 else 0) - (0x14 if (x * 7 + y * 3) % 5 == 0 else 0)
            px[y][x] = (v, v, v + 6, 255)
    big = [[px[y // SCALE][x // SCALE] for x in range(SIZE * SCALE)] for y in range(SIZE * SCALE)]
    out = Path(__file__).resolve().parent.parent / "icons/vastcompressed.png"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(png(big))
    print(out)


if __name__ == "__main__":
    main()
