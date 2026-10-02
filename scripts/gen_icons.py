"""Generate Quantum launcher + brand icons from the source logo.

Usage: python scripts/gen_icons.py <source-image> [out-root]

Outputs:
  android/art/quantum_logo.png                     -- 1024px brand source
  res/mipmap-*/ic_launcher.png                     -- legacy square launcher (48..192)
  res/mipmap-*/ic_launcher_round.png               -- legacy circular launcher
  res/drawable-xxxhdpi/ic_launcher_foreground.png  -- adaptive foreground (432, 66dp safe zone)
  res/drawable-xxxhdpi/ic_launcher_monochrome.png  -- themed-icon layer (luminance -> white alpha)
  res/mipmap-anydpi-v26/ic_launcher.xml            -- rewired to the generated layers
  assets/brand/sidebar_logo.png                    -- sidebar brand asset (1024px)
The default vector placeholder drawable/ic_launcher_foreground.xml is removed
(the PNG of the same name takes over).
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
src_path = Path(sys.argv[1])
out_root = Path(sys.argv[2]) if len(sys.argv) > 2 else root

res = out_root / "android" / "app" / "src" / "main" / "res"
art = out_root / "android" / "art"
brand = out_root / "android" / "app" / "src" / "main" / "assets" / "brand"
for d in (res, art, brand):
    d.mkdir(parents=True, exist_ok=True)

img = Image.open(src_path).convert("RGB")
side = min(img.size)
img = img.crop(((img.width - side) // 2, (img.height - side) // 2,
                (img.width + side) // 2, (img.height + side) // 2))
if side > 1024:
    img = img.resize((1024, 1024), Image.LANCZOS)
logo_path = art / "quantum_logo.png"
img.save(logo_path)


def circular(im: Image.Image, size: int) -> Image.Image:
    big = size * 4
    m = Image.new("L", (big, big), 0)
    ImageDraw.Draw(m).ellipse((8, 8, big - 8, big - 8), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im.resize((size, size), Image.LANCZOS), (0, 0), m)
    return out


for dpi, px in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
    d = res / f"mipmap-{dpi}"
    d.mkdir(exist_ok=True)
    img.resize((px, px), Image.LANCZOS).save(d / "ic_launcher.png")
    circular(img, px).save(d / "ic_launcher_round.png")

CANVAS, SAFE = 432, 288  # adaptive 108dp canvas, logo inside the 66dp safe zone @xxxhdpi
fg = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
inner = img.resize((SAFE, SAFE), Image.LANCZOS)
fg.paste(inner, ((CANVAS - SAFE) // 2, (CANVAS - SAFE) // 2))
fg_d = res / "drawable-xxxhdpi"
fg_d.mkdir(exist_ok=True)
fg.save(fg_d / "ic_launcher_foreground.png")

lum = fg.convert("L").point(lambda v: 0 if v < 50 else min(255, (v - 50) * 3))
mono = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
white = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
mono.paste(white, (0, 0), lum)
mono.save(fg_d / "ic_launcher_monochrome.png")

img.save(brand / "sidebar_logo.png")

xml = res / "mipmap-anydpi-v26" / "ic_launcher.xml"
xml.write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
    '    <background android:drawable="@color/ic_launcher_background" />\n'
    '    <foreground android:drawable="@drawable/ic_launcher_foreground" />\n'
    '    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />\n'
    '</adaptive-icon>\n',
    encoding="utf-8",
)

old_fg = res / "drawable" / "ic_launcher_foreground.xml"
if old_fg.exists():
    old_fg.unlink()
print("OK:", logo_path)
