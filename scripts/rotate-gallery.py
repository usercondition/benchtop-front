"""
Rotate the Samples gallery: pick 18 unique designs (3 rows x 6) by backdrop,
never repeating the same print at a different angle.

Row order (visual break in the middle):
  1. cool grey gaming mat
  2. dark studio
  3. darker tabletop mat
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "assets" / "samples" / "pool"
ACTIVE = ROOT / "assets" / "samples"
MANIFEST = POOL / "manifest.json"
INDEX = ROOT / "index.html"

GALLERY_RE = re.compile(
    r'(<ul class="gallery">)(.*?)(</ul>)',
    re.DOTALL,
)


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def seed_for(day: date) -> int:
    digest = hashlib.sha256(day.isoformat().encode()).hexdigest()
    return int(digest[:12], 16)


def designs_by_category(manifest: dict) -> dict[str, list[tuple[str, dict]]]:
    grouped: dict[str, list[tuple[str, dict]]] = {}
    for design_id, meta in manifest["designs"].items():
        cat = meta["category"]
        pick = meta["pick"]
        if not (POOL / f"{pick}.webp").exists():
            continue
        grouped.setdefault(cat, []).append((design_id, meta))
    return grouped


def pick_rows(manifest: dict, day: date) -> list[tuple[str, str, dict]]:
    """Return ordered (design_id, category, meta) for 18 unique designs."""
    rng = random.Random(seed_for(day))
    per_row = int(manifest["per_row"])
    by_cat = designs_by_category(manifest)
    picked: list[tuple[str, str, dict]] = []
    used_designs: set[str] = set()

    for cat in manifest["row_order"]:
        options = [(d, m) for d, m in by_cat.get(cat, []) if d not in used_designs]
        if len(options) < per_row:
            raise SystemExit(
                f"Not enough unique designs for '{cat}': need {per_row}, have {len(options)}"
            )
        choice = rng.sample(options, per_row)
        rng.shuffle(choice)
        for design_id, meta in choice:
            used_designs.add(design_id)
            picked.append((design_id, cat, meta))
    return picked


def sync_active(picked: list[tuple[str, str, dict]]) -> None:
    ACTIVE.mkdir(parents=True, exist_ok=True)
    for old in ACTIVE.glob("img_*.webp"):
        old.unlink()
    for _, _, meta in picked:
        image_id = meta["pick"]
        shutil.copy2(POOL / f"{image_id}.webp", ACTIVE / f"{image_id}.webp")


def rewrite_index(picked: list[tuple[str, str, dict]]) -> None:
    labels = {
        "mat_cool": "cool grey gaming mat",
        "mat_break": "darker warzone mat — visual break",
        "mat_street": "street / asphalt tabletop",
        "studio": "dark studio",
        "mat_dark": "darker tabletop mat",
    }
    body = ""
    last_cat = None
    for _, cat, meta in picked:
        image_id = meta["pick"]
        alt = str(meta.get("alt") or "Resin print sample from client work").replace('"', "&quot;")
        if cat != last_cat:
            body += f'            <!-- Row: {labels.get(cat, cat)} -->\n'
            last_cat = cat
        body += f"""            <li class="gallery__item">
              <img
                src="assets/samples/{image_id}.webp"
                alt="{alt}"
                width="1200"
                height="900"
                loading="lazy"
                decoding="async"
              />
            </li>
"""

    html = INDEX.read_text(encoding="utf-8")
    match = GALLERY_RE.search(html)
    if not match:
        raise SystemExit('Could not find <ul class="gallery"> in index.html')
    new_html = (
        html[: match.start()]
        + match.group(1)
        + "\n"
        + body
        + "          "
        + match.group(3)
        + html[match.end() :]
    )
    INDEX.write_text(new_html, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate Samples gallery photos")
    parser.add_argument("--date", help="YYYY-MM-DD seed (default: today UTC)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    day = date.fromisoformat(args.date) if args.date else datetime.now(timezone.utc).date()
    manifest = load_manifest()
    picked = pick_rows(manifest, day)

    print(f"rotation date={day.isoformat()} seed={seed_for(day)}")
    print(f"unique designs={len(picked)} (no angle duplicates)")
    for i, (design_id, cat, meta) in enumerate(picked, 1):
        print(f"  {i:02d} [{cat}] {design_id} -> {meta['pick']}")

    if args.dry_run:
        return

    sync_active(picked)
    rewrite_index(picked)
    print("updated assets/samples/ and index.html")


if __name__ == "__main__":
    main()
