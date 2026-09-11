import csv
import math
from pathlib import Path

import cadquery as cq
from ocp_vscode import show

MANIFEST_PATH = Path("output/manifest.csv")
MARGIN = 20  # spacing between variants (mm)


def load_ok_variants():
    variants = []
    with open(MANIFEST_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["status"] == "ok":
                variants.append(row)
    return variants


def main():
    variants = load_ok_variants()
    if not variants:
        print("No variants with status 'ok' to show.")
        return

    parts = []
    names = []
    max_size = 0.0

    for row in variants:
        # Import the STEP file itself, to check what was actually exported.
        # step_file in the manifest is relative to the output dir, hence
        # MANIFEST_PATH.parent.
        step_path = MANIFEST_PATH.parent / row["step_file"]
        part = cq.importers.importStep(str(step_path))
        bbox = part.val().BoundingBox()
        max_size = max(max_size, bbox.xlen, bbox.ylen)
        parts.append(part)
        names.append(row["variant_id"])

    spacing = max_size + MARGIN
    cols = math.ceil(math.sqrt(len(parts)))

    placed_parts = []
    for i, part in enumerate(parts):
        row_idx = i // cols
        col_idx = i % cols
        x = col_idx * spacing
        y = -row_idx * spacing
        placed_parts.append(part.translate((x, y, 0)))

    show(*placed_parts, names=names)
    print(f"{len(placed_parts)} variants shown in viewer: {', '.join(names)}")


if __name__ == "__main__":
    main()
