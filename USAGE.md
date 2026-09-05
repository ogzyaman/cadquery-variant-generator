# Usage

This package generates a set of part variants from a dimension table.
Edit the table, run one command, and every variant is exported.

## Setup

Install the environment once:

```
conda create -n cad python=3.11
conda activate cad
conda install -c conda-forge cadquery openpyxl vtk
```

## Defining variants

Open `variants.csv`. Each row is one variant.

| Column | Meaning | Unit |
|---|---|---|
| variant_id | Identifier used for the file names | text |
| length_mm | Overall length | mm |
| width_mm | Overall width | mm |
| height_mm | Plate thickness | mm |
| hole_dia_mm | Diameter of the centre hole | mm |
| fillet_r_mm | Corner fillet radius | mm |

All dimensions are in millimetres. Use a full stop as the decimal
separator, not a comma.

If you leave `variant_id` empty, identifiers are assigned automatically
as V001, V002 and so on. Identifiers must be unique.

The file can be edited in Excel. If the columns do not separate correctly
when you double-click the file, open Excel first and use
Data > From Text/CSV, with the comma as the delimiter.

## Running

```
conda activate cad
python generate_variants.py
```

To generate only one format:

```
python generate_variants.py variants.csv output --formats step
python generate_variants.py variants.csv output --formats stl
```

## Output

```
output/
├── manifest.csv     the same table, plus output paths and status
├── manifest.xlsx    Excel version of the manifest
├── step/            one STEP file per variant
├── stl/             one STL file per variant
└── preview/         rendered images
```

Open `manifest.xlsx` to see which file belongs to which set of dimensions.
The `status` column reads `ok` for every variant that was exported.

## If something goes wrong

The generator checks the whole table before it builds anything. If a row
has a missing value, a non-numeric entry or a repeated identifier, no
files are written and every problem is listed at once. Correct the table
and run again.

A row can also fail during the build, usually because the dimensions are
geometrically impossible. A fillet radius larger than half the width is
the common case. That row is marked `failed` in the manifest with the
reason, and the remaining variants are still generated.

## Preview images

```
python render_preview.py                      all variants, laid out in a grid
python render_detail.py --variant-id V013     one variant, close up
```

Both read the manifest and require STL output.
