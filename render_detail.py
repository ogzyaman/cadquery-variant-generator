import argparse
import csv
import sys
from pathlib import Path

from render_preview import build_actor, render_scene


def find_variant(manifest_path, variant_id):
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["variant_id"] == variant_id:
                return row
    return None


def main():
    parser = argparse.ArgumentParser(description="Close-up isometric render of a single variant (VTK, headless).")
    parser.add_argument("--variant-id", default="V013")
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "manifest.csv"

    row = find_variant(manifest_path, args.variant_id)
    if row is None:
        sys.exit(f"ERROR: variant_id not found: {args.variant_id}")
    if row["status"] != "ok":
        sys.exit(f"ERROR: variant {args.variant_id} status='{row['status']}', cannot render")
    if "stl_file" not in row:
        sys.exit("ERROR: STL is required for preview rendering. Regenerate with --formats stl or step,stl.")

    stl_path = output_dir / row["stl_file"]
    actor, bounds = build_actor(stl_path)

    output_path = output_dir / "preview" / "detail.png"
    render_scene([actor], args.width, args.height, output_path, direction=(1, -1, 1), view_up=(0, 0, 1))

    print(f"{args.variant_id} rendered -> {output_path} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
