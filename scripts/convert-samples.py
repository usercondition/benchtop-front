"""Convert HEIC samples to WebP for gallery/review."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

src = Path(sys.argv[1])
dest = Path(sys.argv[2])
mode = sys.argv[3] if len(sys.argv) > 3 else "review"
names = sys.argv[4:]

dest.mkdir(parents=True, exist_ok=True)
max_edge = 1200 if mode == "gallery" else 720
quality = 74 if mode == "gallery" else 68

if names:
    files = []
    for n in names:
        p = src / (n if n.lower().endswith(".heic") else f"{n}.HEIC")
        if not p.exists():
            p = src / f"{Path(n).stem}.heic"
        files.append(p)
else:
    files = sorted(src.glob("*.HEIC")) + sorted(src.glob("*.heic"))
    # de-dupe case-insensitive
    seen = set()
    uniq = []
    for f in files:
        key = f.name.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    files = uniq

ok = fail = 0
for path in files:
    if not path.exists():
        print("missing", path)
        fail += 1
        continue
    out = dest / f"{path.stem.lower()}.webp"
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            im.save(out, "WEBP", quality=quality, method=4)
        ok += 1
        if ok % 25 == 0:
            print(f"… {ok}/{len(files)}")
    except Exception as e:
        fail += 1
        print("fail", path.name, e)

print(f"done ok={ok} fail={fail} -> {dest}")
