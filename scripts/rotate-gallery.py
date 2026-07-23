"""
Rotate the Samples gallery: pick 18 photos (3 rows x 6) by backdrop category,
copy them into assets/samples/, and rewrite the gallery block in index.html.

Same logic as the hand-curated layout:
  row 1 = cool grey gaming mat
  row 2 = dark studio (visual break)
  row 3 = darker tabletop mat
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
    # Stable daily seed so re-runs the same day keep the same set
    digest = hashlib.sha256(day.isoformat().encode()).hexdigest()
    return int(digest[:12], 16)


def pick_rows(manifest: dict, day: date) -> list[tuple[str, str]]:
    """Return ordered list of (id, category) for 18 slots."""
    rng = random.Random(seed_for(day))
    per_row = int(manifest["per_row"])
    row_order = list(manifest["row_order"])
    categories = manifest["categories"]
    picked: list[tuple[str, str]] = []
    used: set[str] = set()

    for cat in row_order:
        ids = [i for i in categories[cat]["ids"] if (POOL / f"{i}.webp").exists()]
        available = [i for i in ids if i not in used]
        if len(available) < per_row:
            raise SystemExit(
                f"Not enough pool images for category '{cat}': need {per_row}, have {len(available)}"
            )
        choice = rng.sample(available, per_row)
        # Mild within-row shuffle so order isn't always filename-sorted
        rng.shuffle(choice)
        for image_id in choice:
            used.add(image_id)
            picked.append((image_id, cat))
    return picked


def sync_active(picked: list[tuple[str, str]]) -> None:
    ACTIVE.mkdir(parents=True, exist_ok=True)
    # Remove previous active webps (keep pool/)
    for old in ACTIVE.glob("img_*.webp"):
        old.unlink()
    for image_id, _ in picked:
        src = POOL / f"{image_id}.webp"
        shutil.copy2(src, ACTIVE / f"{image_id}.webp")


def item_html(image_id: str, alt: str, comment: str | None = None) -> str:
    src = f"assets/samples/{image_id}.webp"
    block = ""
    if comment:
        block += f"            <!-- {comment} -->\n"
    block += f"""            <li class="gallery__item">
              <img
                src="{src}"
                alt="{alt}"
                width="1200"
                height="900"
                loading="lazy"
                decoding="async"
              />
            </li>
"""
    return block


def rewrite_index(picked: list[tuple[str, str]], manifest: dict) -> None:
    alts = manifest.get("alts", {})
    labels = {k: v["label"] for k, v in manifest["categories"].items()}
    body = ""
    last_cat = None
    for image_id, cat in picked:
        comment = None
        if cat != last_cat:
            comment = f"Row: {labels.get(cat, cat)}"
            last_cat = cat
        alt = alts.get(image_id, "Resin print sample from client work")
        # Escape quotes in alt
        alt = alt.replace('"', "&quot;")
        body += item_html(image_id, alt, comment)

    html = INDEX.read_text(encoding="utf-8")
    match = GALLERY_RE.search(html)
    if not match:
        raise SystemExit("Could not find <ul class=\"gallery\"> in index.html")
    new_html = html[: match.start()] + match.group(1) + "\n" + body + "          " + match.group(3) + html[match.end() :]
    INDEX.write_text(new_html, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate Samples gallery photos")
    parser.add_argument(
        "--date",
        help="YYYY-MM-DD to seed the rotation (default: today UTC)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selection only; do not write files",
    )
    args = parser.parse_args()

    if args.date:
        day = date.fromisoformat(args.date)
    else:
        day = datetime.now(timezone.utc).date()

    manifest = load_manifest()
    picked = pick_rows(manifest, day)

    print(f"rotation date={day.isoformat()} seed={seed_for(day)}")
    for i, (image_id, cat) in enumerate(picked, 1):
        print(f"  {i:02d} [{cat}] {image_id}")

    if args.dry_run:
        return

    sync_active(picked)
    rewrite_index(picked, manifest)
    print("updated assets/samples/ and index.html")


if __name__ == "__main__":
    main()
