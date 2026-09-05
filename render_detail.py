import argparse
import csv
import math
import sys
from pathlib import Path

from render_preview import build_actor, fit_camera_tight, render_scene, set_camera_direction


def find_variant(manifest_path, variant_id):
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["variant_id"] == variant_id:
                return row
    return None


def main():
    parser = argparse.ArgumentParser(description="Tek varyant için yakın çekim izometrik render (VTK, headless).")
    parser.add_argument("--variant-id", default="V013")
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "manifest.csv"

    row = find_variant(manifest_path, args.variant_id)
    if row is None:
        sys.exit(f"HATA: variant_id bulunamadı: {args.variant_id}")
    if row["status"] != "ok":
        sys.exit(f"HATA: variant {args.variant_id} status='{row['status']}', render edilemez")
    if "stl_file" not in row:
        sys.exit("HATA: Preview render için STL gerekli. --formats stl veya step,stl ile yeniden üretin.")

    stl_path = output_dir / row["stl_file"]
    actor, bounds = build_actor(stl_path)

    output_path = output_dir / "preview" / "detail.png"
    render_scene([actor], args.width, args.height, output_path, direction=(1, -1, 1), view_up=(0, 0, 1))

    print(f"{args.variant_id} render edildi -> {output_path} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
