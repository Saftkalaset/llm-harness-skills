# Upstream Provenance: 3D Print Spec & Dimension Extractor

This document records the upstream tools, specifications, standards, and community techniques evaluated for the `3d-print-spec-extractor` skill. Refer to these references when updating image measurement pipelines, calibration routines, or tolerance models.

## Provenance Ledger

| Source / Standard | Specification / Repository | Version / Tag | Evaluation Date | Origin Classification | Borrowed Concepts | Local Divergence / Customizations | Re-evaluation Triggers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pillow (PIL) & EXIF Orientation Standard** | [python-pillow/Pillow](https://github.com/python-pillow/Pillow) / [JEITA CP-3451](https://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf) | Pillow 10.x / 11.x (CP-3451 Tag 274) | 2026-10-11 (initial) / 2026-10-23 | Runtime library & standard | EXIF Tag 274 orientation handling via `ImageOps.exif_transpose`, image cropping, gamma adjustment pipelines. | Integrated phone photo normalization and shadow-lifting into a single CLI step (`crop --gamma 0.4`) specifically tuned for dark/black 3D printed parts. | Upstream support for advanced mobile camera containers (HDR gain maps, HEIC/AVIF depth maps) or automatic orientation fixes. |
| **NumPy Spatial Calibration & Bounding Boxes** | [numpy/numpy](https://github.com/numpy/numpy) | NumPy 1.26+ | 2026-10-11 (initial) / 2026-10-23 | Runtime library | Array masking, pixel thresholding, bounding-box calculation (`bbox`). | Converted raw pixel spans into physical CAD dimensions via explicit planar calibration (`--px` / `--mm`), with uncertainty tracking and diametral vs. radial clearance modeling. | Upstream computer vision helpers or automated fiducial detection (ArUco / OpenCV) becoming lightweight and portable. |

---

## Technical Notes

### 1. EXIF Tag 274 Handling
Smartphone photos frequently store unrotated pixel arrays and set EXIF orientation flags (1-8). Agents analyzing raw pixel arrays without EXIF transposition miscalculate aspect ratios, feature widths, and heights. `measure_reference.py` automatically normalizes images using `ImageOps.exif_transpose` before performing calibration or bounding box measurements.

### 2. Planar Calibration Constraints
Pixel-to-millimeter ratios (`px/mm`) are mathematically valid only within the specific plane of calibration. Measurements taken across perspective planes or lens-distorted peripheries must be labeled as estimates with stated uncertainty bounds rather than verified dimensions.
