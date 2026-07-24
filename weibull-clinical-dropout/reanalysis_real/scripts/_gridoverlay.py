"""Overlay a pixel grid on a figure to read axis-calibration anchor pixels.
Not part of the reproducible pipeline output; a helper for manual calibration."""
import sys
from PIL import Image, ImageDraw

src = sys.argv[1]
dst = sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 50
im = Image.open(src).convert("RGB")
d = ImageDraw.Draw(im)
W, H = im.size
for x in range(0, W, step):
    d.line([(x, 0), (x, H)], fill=(0, 0, 0), width=1)
    d.text((x + 1, 1), str(x), fill=(255, 0, 255))
for y in range(0, H, step):
    d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
    d.text((1, y + 1), str(y), fill=(255, 0, 255))
im.save(dst)
print(f"{src} size={W}x{H} -> {dst}")
