import argparse
import csv
import math
import sys
from pathlib import Path

import vtk

X_PADDING_FACTOR = 1.20  # relative to the longest part's length
Y_PADDING_FACTOR = 1.20  # relative to the widest part's width
LABEL_GAP_MM = 6  # gap between a part's bottom edge and its label
LABEL_RESERVE_MM = 22  # estimated vertical space a label needs, between/below rows
LABEL_FONT_SIZE = 32  # pixels -- vtkTextActor is a 2D overlay, doesn't scale with world units
LABEL_COLOR = (0.25, 0.25, 0.25)


def load_ok_variants(manifest_path):
    variants = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["status"] == "ok":
                variants.append(row)
    return variants


def build_actor(stl_path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(stl_path))
    reader.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    prop = actor.GetProperty()
    prop.SetColor(0.55, 0.65, 0.78)
    prop.SetAmbient(0.2)
    prop.SetDiffuse(0.8)
    prop.SetSpecular(0.25)
    prop.SetSpecularPower(15)

    return actor, reader.GetOutput().GetBounds()


def add_world_label(renderer, text, world_x, world_y, font_size=LABEL_FONT_SIZE, color=LABEL_COLOR):
    """2D overlay text (vtkTextActor, system font) -- supports Unicode characters
    like Ø (vtkVectorText did not). Anchored to World coordinates, so VTK
    recomputes its screen position from the camera on every render. Font size
    is a fixed pixel value that doesn't scale with world zoom."""
    text_actor = vtk.vtkTextActor()
    text_actor.SetInput(text)

    prop = text_actor.GetTextProperty()
    prop.SetFontFamilyToArial()
    prop.SetFontSize(font_size)
    prop.SetColor(*color)
    prop.SetJustificationToCentered()
    prop.SetVerticalJustificationToTop()

    coord = text_actor.GetPositionCoordinate()
    coord.SetCoordinateSystemToWorld()
    coord.SetValue(world_x, world_y, 0)

    renderer.AddActor(text_actor)


def set_camera_direction(camera, center, direction, view_up, distance):
    norm = math.sqrt(sum(c * c for c in direction))
    camera.SetFocalPoint(*center)
    camera.SetPosition(
        center[0] + direction[0] * distance / norm,
        center[1] + direction[1] * distance / norm,
        center[2] + direction[2] * distance / norm,
    )
    camera.SetViewUp(*view_up)


def fit_camera_tight(camera, bounds, aspect, padding=1.08):
    """Frames the camera tightly around bounds: projects the corners onto the
    camera plane and computes ParallelScale from the actual width/height ratio
    (the generic ResetCamera() leaves too much padding at arbitrary angles)."""
    position = camera.GetPosition()
    focal = camera.GetFocalPoint()
    view_up = camera.GetViewUp()

    dop = [focal[i] - position[i] for i in range(3)]
    dop_len = math.sqrt(sum(c * c for c in dop))
    dop = [c / dop_len for c in dop]

    def cross(a, b):
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    def normalize(v):
        n = math.sqrt(sum(c * c for c in v))
        return tuple(c / n for c in v)

    right = normalize(cross(dop, view_up))
    up = normalize(cross(right, dop))

    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    corners = [(x, y, z) for x in (xmin, xmax) for y in (ymin, ymax) for z in (zmin, zmax)]

    us, vs = [], []
    for c in corners:
        rel = [c[i] - focal[i] for i in range(3)]
        us.append(sum(rel[i] * right[i] for i in range(3)))
        vs.append(sum(rel[i] * up[i] for i in range(3)))

    u_extent = max(us) - min(us)
    v_extent = max(vs) - min(vs)

    half_height = max(v_extent / 2, (u_extent / 2) / aspect)
    camera.SetParallelScale(half_height * padding)


def render_scene(
    actors,
    width,
    height,
    output_path,
    direction=(0, 0, 1),
    view_up=(0, 1, 0),
    padding=1.08,
    labels=None,
    bottom_margin=0,
):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.97, 0.97, 0.97)
    renderer.SetBackground2(0.90, 0.90, 0.90)
    renderer.GradientBackgroundOn()
    for actor in actors:
        renderer.AddActor(actor)

    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    render_window.SetSize(width, height)
    render_window.AddRenderer(renderer)

    camera = renderer.GetActiveCamera()
    camera.SetParallelProjection(True)

    bounds = list(renderer.ComputeVisiblePropBounds())
    bounds[2] -= bottom_margin  # extra room below the last row, for labels
    bounds = tuple(bounds)

    center = (
        (bounds[0] + bounds[1]) / 2,
        (bounds[2] + bounds[3]) / 2,
        (bounds[4] + bounds[5]) / 2,
    )
    diagonal = math.dist(bounds[0::2], bounds[1::2])

    # The default headlight is attached to the camera: a straight top-down
    # view then has light hitting the surface head-on, giving a flat, contrast-
    # less image. Two fixed-angle lights (key + fill) keep shading even then.
    renderer.AutomaticLightCreationOff()
    light_distance = diagonal * 3

    key_light = vtk.vtkLight()
    key_light.SetLightTypeToSceneLight()
    key_light.SetPosition(center[0] + light_distance, center[1] - light_distance, center[2] + light_distance * 1.5)
    key_light.SetFocalPoint(*center)
    key_light.SetIntensity(0.9)
    renderer.AddLight(key_light)

    fill_light = vtk.vtkLight()
    fill_light.SetLightTypeToSceneLight()
    fill_light.SetPosition(center[0] - light_distance, center[1] + light_distance, center[2] + light_distance)
    fill_light.SetFocalPoint(*center)
    fill_light.SetIntensity(0.35)
    renderer.AddLight(fill_light)

    set_camera_direction(camera, center, direction=direction, view_up=view_up, distance=diagonal * 2)
    renderer.ResetCameraClippingRange()
    fit_camera_tight(camera, bounds, aspect=width / height, padding=padding)

    if labels:
        for text, x, y in labels:
            add_world_label(renderer, text, x, y)

    render_window.Render()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    window_to_image = vtk.vtkWindowToImageFilter()
    window_to_image.SetInput(render_window)
    window_to_image.SetInputBufferTypeToRGB()
    window_to_image.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(window_to_image.GetOutputPort())
    writer.Write()


def main():
    parser = argparse.ArgumentParser(description="Grid preview render of all variants (VTK, headless).")
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--cols", type=int, default=5)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "manifest.csv"

    variants = load_ok_variants(manifest_path)
    if not variants:
        print("No variants with status 'ok' to render.")
        return

    if "stl_file" not in variants[0]:
        sys.exit("ERROR: STL is required for preview rendering. Regenerate with --formats stl or step,stl.")

    parts = []
    max_xlen = 0.0
    max_ylen = 0.0
    for row in variants:
        stl_path = output_dir / row["stl_file"]
        actor, bounds = build_actor(stl_path)
        xlen = bounds[1] - bounds[0]
        ylen = bounds[3] - bounds[2]
        max_xlen = max(max_xlen, xlen)
        max_ylen = max(max_ylen, ylen)
        parts.append((row, actor, bounds))

    x_spacing = max_xlen * X_PADDING_FACTOR
    y_spacing = max_ylen * Y_PADDING_FACTOR + LABEL_RESERVE_MM
    cols = args.cols

    actors = []
    labels = []
    for i, (row, actor, bounds) in enumerate(parts):
        row_idx = i // cols
        col_idx = i % cols
        x = col_idx * x_spacing
        y = -row_idx * y_spacing
        actor.SetPosition(x, y, 0)
        actors.append(actor)

        label_text = (
            f"{row['variant_id']}  "
            f"{int(float(row['length_mm']))}x{int(float(row['width_mm']))}x{int(float(row['height_mm']))}  "
            f"Ø{int(float(row['hole_dia_mm']))}"
        )
        part_center_x = x + (bounds[0] + bounds[1]) / 2
        part_bottom_y = y + bounds[2]
        label_top_y = part_bottom_y - LABEL_GAP_MM
        labels.append((label_text, part_center_x, label_top_y))

    output_path = output_dir / "preview" / "grid.png"
    render_scene(
        actors,
        args.width,
        args.height,
        output_path,
        padding=1.05,
        labels=labels,
        bottom_margin=LABEL_RESERVE_MM,
    )

    print(f"{len(parts)} variants rendered -> {output_path} ({args.width}x{args.height}, {cols} columns)")


if __name__ == "__main__":
    main()
