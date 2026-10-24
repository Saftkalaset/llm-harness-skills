---
name: 3d-print-spec-extractor
description: >-
  Extracts physical dimensions, port locations, clearances, and tolerances from reference photos, product pages, and datasheets for 3D printing. Use whenever modeling parts to fit real-world products.
---

# 3D Print Spec & Dimension Extractor

Use this skill to gather and report physical dimensions from manufacturer photos, specifications, or product links. Delegate independent reference lookup to a research worker when available and authorized; otherwise research directly. Give it a short brief and request a specification table plus design-relevant uncertainties, not the full conversation. Distinguish sourced dimensions from estimates, and do not present image-derived estimates as precise measurements.

## Workflow

### 1. Acquire & Orient Clean Reference Images
- Prefer manufacturer drawings, datasheets, and direct caliper measurements. If downloading images, use a temporary scratch directory and retain the source URL:
  ```bash
  curl -s -L -o scratch/ref_image.png "<image_url>"
  ```
- **Phone Photos (EXIF Orientation & Dark Shadows):** Smartphone photos (`IMG_*.JPG`) often store rotation in EXIF Tag 274 and underexpose dark/black printed parts in shadow. Before viewing or measuring a phone photo, normalize its EXIF orientation and (if dark) lift shadows with `--gamma 0.4` in a single call:
  ```bash
  python3 <skill-directory>/scripts/measure_reference.py crop --image "<photo.jpg>" --gamma 0.4 --out scratch/upright.jpg
  ```
- Prioritize straight-on orthographic or flat perspective shots over angled hero renders when available.
- A single scale applies only to features on approximately the same plane as the calibration feature. Perspective, lens distortion, and depth differences introduce error. Do not claim precision from an angled image; report the limitation or find a better reference.

### 2. Calibrate Scale (px/mm)
Find a known feature in the image to establish the pixel-to-millimeter ratio:
* **Calibration:** Prefer a dimension stated for the exact product or a clearly visible feature in the same plane. Generic connector dimensions depend on whether the plug, receptacle, or surrounding housing is being measured; use them only as rough checks, not precision calibration.

Resolve the bundled script relative to this skill's directory (the directory containing `SKILL.md`), then calculate the scale:
```bash
python3 <skill-directory>/scripts/measure_reference.py calibrate --px <measured_pixels> --mm <known_mm>
```

### 3. Measure Unknown Features
Crop tightly around the target and measure its selected pixel span (`measure_reference.py` automatically applies `ImageOps.exif_transpose` on load). `bbox` finds all non-background pixels in an image; it does not identify a particular feature and may include shadows, labels, or other objects. Use image inspection or explicit coordinates to select the intended feature:
```bash
python3 <skill-directory>/scripts/measure_reference.py bbox --image scratch/crop.png --scale <calibrated_scale>
```

Record the source URL/file, view and measurement plane, calibration feature, pixel span, scale, and estimated uncertainty. Label every value as manufacturer-specified, directly measured, image-derived, or estimated. If perspective or occlusion makes a measurement unreliable, say so and request a better source or direct measurement.

### 4. Convert evidence into fit targets

- State both per-side/radial and total/diametral clearance (`ID = OD + 2c`). Separate nominal hardware size, CAD allowance and measured as-printed size.
- Bore compensation depends on actual nozzle, extrusion width, material, orientation and calibration. Do not assert a fixed printer-wide shrinkage correction. For an uncalibrated slip fit, a small coupon with several allowances is more reliable than a full print; record the selected value and its process.
- Preserve user-confirmed interfaces unless new evidence requires changing them. Manufacturer CAD establishes nominal geometry, not an as-built tolerance guarantee.
- Include shoulders, feet, ridges, complete plug bodies and cable bends; connector-opening bounds alone do not prove insertion/access.
- Distinguish bounding envelopes from actual vents/contact surfaces. A percentage projected overlap is not airflow or thermal-performance loss.
- For horizontal roofs, peaked profiles can reduce supports; rounded crowns and bridges depend on the actual process and span. Label support requirements and verify in the slice rather than declaring universal support-free angles.
- Cache values with source URL/file, method, frame, uncertainty and source-geometry revision/fingerprint. Reuse matching evidence; remeasure changed or contradicted records. Keep machine-specific calibration separate from shared defaults.

### 5. Standard Output Format (Matches `PROJECT.md` Section 2)
Return a concise mechanical specification table and any critical limitations or missing measurements affecting the design. Include manufacturer-specified, directly measured, image-derived or estimated status in the source column. Example format:

```markdown
### Mechanical Spec Sheet: [Product / Component Name]
* **Reference Scale:** 20.23 px/mm (only for the calibrated image plane; include source and uncertainty)

| Feature | Nominal | Clearance | **CAD Target** | Source / Confidence |
| :--- | ---: | ---: | ---: | :--- |
| Stand Base Column Ø | 60.0 | +0.20 /side (+0.40 Ø) | **60.40 ID** | Manufacturer nominal; allowance is a starting target pending printed coupon |
| Cable Cutout (W × H) | 11.5 × 7.0 | +2.25 /side (+4.5 total W/H) | **16.0 × 11.5** | Measured plug envelope; allow bend/access space separately; verify supports |
```
