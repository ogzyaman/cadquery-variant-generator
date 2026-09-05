# Delivery

This package contains the generated part variants.

## Contents

```
step/           one STEP file per variant
stl/            one STL file per variant
manifest.xlsx   the dimension table with the file name of each variant
manifest.csv    the same table in plain text
preview/        rendered images of the set
```

## Reading the manifest

Open `manifest.xlsx`. Each row is one variant. The columns hold the
dimensions used, the exported file names and a status.

To find the file for a given set of dimensions, filter the table on the
dimension columns and read the file name from the same row. To go the
other way, search for the file name.

Variants with a status other than `ok` were not exported. The reason is
given in the same cell.

## Units and conventions

All dimensions are in millimetres. The parts are modelled at the origin
with the base on the XY plane.

STEP files carry the full geometry and are suitable for CAM, drawing
creation and further modelling. STL files are a triangulated
approximation, intended for 3D printing and visualisation, and should
not be used for machining or dimensional checks.

## Revisions

To change a dimension or add a variant, send the updated values and the
affected variant identifiers. The set is regenerated from the same
definition, so existing variants remain identical unless their
dimensions change.
