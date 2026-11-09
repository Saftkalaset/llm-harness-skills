#!/usr/bin/env python3
"""Small, dependency-free plan calculations. Does not certify geometry or safety."""

import argparse
import json
import math
from pathlib import Path


def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{label} must be finite" + (" and positive" if positive else ""))
    return float(value)


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("points must contain two coordinates")
    return [number(value[0], "x"), number(value[1], "y")]


def polygon_area(points):
    if len(points) < 3:
        raise ValueError("a polygon requires at least three points")
    points = [point(p) for p in points]
    # Translate first to avoid unnecessary cancellation at large source offsets.
    origin = points[0]
    points = [[x - origin[0], y - origin[1]] for x, y in points]
    return abs(sum(x * points[(i + 1) % len(points)][1]
                   - points[(i + 1) % len(points)][0] * y
                   for i, (x, y) in enumerate(points))) / 2


def bounds(rect):
    x, y = number(rect["x"], "x"), number(rect["y"], "y")
    w = number(rect["width"], "width", positive=True)
    h = number(rect["height"], "height", positive=True)
    return ((x, x + w), (y, y + h))


def axis_index(axis):
    if axis not in ("x", "y"):
        raise ValueError("axis must be x or y")
    return 0 if axis == "x" else 1


def opposed_gap(a, b, axis, scale):
    """Return signed gap only when the perpendicular projections overlap."""
    index = axis_index(axis)
    a, b = bounds(a), bounds(b)
    other = 1 - index
    overlap = min(a[other][1], b[other][1]) - max(a[other][0], b[other][0])
    if overlap <= 0:
        return None
    return max(b[index][0] - a[index][1], a[index][0] - b[index][1]) / scale


def calibration(*, pixel_span=None, length_m=None, dpi=None,
                denominator=None, image_factor=1.0):
    if pixel_span is not None or length_m is not None:
        if dpi is not None or denominator is not None or image_factor != 1.0:
            raise ValueError("use a known span OR scan metadata, not both")
        scale = number(pixel_span, "pixel span", True) / number(length_m, "length", True)
        return {"pixels_per_metre": scale, "method": "known_span"}
    scale = (number(dpi, "dpi", True) / 25.4 * 1000
             / number(denominator, "scale denominator", True)
             * number(image_factor, "image factor", True))
    return {"pixels_per_metre": scale, "method": "scan_metadata_candidate",
            "limitation": "Requires confirmation of reproduction size and transforms."}


def audit(model):
    source = model["source"]
    scale = number(source["pixels_per_metre"], "pixels_per_metre", True)
    if source["scale_status"] not in {"dimension-derived", "scan-derived",
                                      "area-normalized", "unverified"}:
        raise ValueError("unknown scale_status")
    result = {"scale_status": source["scale_status"], "pixels_per_metre": scale,
              "zone_areas_m2": {}, "variants": [], "issues": [],
              "limitations": ["Zone sum does not verify overlap, coverage, holes or self-intersections.",
                              "Rectangles are axis-aligned; gaps are closed-envelope geometry unless otherwise supplied.",
                              "This is not a structural, installation or compliance assessment."]}
    if source["scale_status"] == "unverified":
        result["issues"].append("Scale is unverified; physical dimensions remain hypothetical.")
    for zone in model.get("zones", []):
        name = zone["id"]
        if name in result["zone_areas_m2"]:
            raise ValueError(f"duplicate zone id: {name}")
        result["zone_areas_m2"][name] = polygon_area(zone["polygon"]) / scale ** 2
    result["zone_sum_m2"] = sum(result["zone_areas_m2"].values())
    if "reference_area_m2" in source and result["zone_areas_m2"]:
        target = number(source["reference_area_m2"], "reference area", True)
        result["reference_area_m2"] = target
        result["area_difference_m2"] = result["zone_sum_m2"] - target
        result["area_difference_percent"] = 100 * (result["zone_sum_m2"] / target - 1)
        # Never normalize the source silently.
    fixed = model.get("fixed_geometry", {})
    names = set()
    for variant in model.get("variants", []):
        name = variant["id"]
        if name in names:
            raise ValueError(f"duplicate variant id: {name}")
        names.add(name)
        report = {"id": name, "fixed_geometry": [], "clearances": [], "boundaries": []}
        geometry = variant.get("geometry", {})
        for feature, expected in fixed.items():
            status = "missing" if feature not in geometry else "unchanged" if geometry[feature] == expected else "changed"
            report["fixed_geometry"].append({"id": feature, "status": status})
            if status != "unchanged":
                result["issues"].append(f"{name}: fixed geometry {feature} {status}")
        rectangles = variant.get("rectangles", {})
        for value in rectangles.values():
            bounds(value)
        for check in variant.get("clearances", []):
            minimum = number(check["minimum_m"], "minimum_m")
            uncertainty = number(check.get("uncertainty_m", 0), "uncertainty_m")
            if minimum < 0 or uncertainty < 0:
                raise ValueError("minimum and uncertainty must be nonnegative")
            gap = opposed_gap(rectangles[check["a"]], rectangles[check["b"]], check["axis"], scale)
            entry = {"id": check["id"], "constraint_source": check["constraint_source"],
                     "state": check.get("state", "closed"), "minimum_m": minimum,
                     "gap_m": gap, "status": "not_opposed" if gap is None else "computed",
                     "nominal_pass": None if gap is None else gap + 1e-9 >= minimum,
                     "uncertainty_m": uncertainty,
                     "lower_bound_pass": None if gap is None else gap - uncertainty + 1e-9 >= minimum}
            report["clearances"].append(entry)
            if gap is None or not entry["lower_bound_pass"]:
                result["issues"].append(f"{name}: clearance {check['id']} unresolved or below minimum")
        for check in variant.get("boundaries", []):
            axis = axis_index(check["axis"])
            if check["edge"] not in ("min", "max") or check["relation"] not in ("<=", ">="):
                raise ValueError("boundary needs min/max edge and <=/>= relation")
            edge = bounds(rectangles[check["rect"]])[axis][check["edge"] == "max"]
            limit = number(check["limit"], "boundary limit")
            margin = (limit - edge if check["relation"] == "<=" else edge - limit) / scale
            passed = margin >= -1e-9
            report["boundaries"].append({"id": check["id"], "margin_m": margin,
                                         "crossing_m": max(0, -margin), "within": passed,
                                         "constraint_source": check["constraint_source"]})
            if not passed:
                result["issues"].append(f"{name}: boundary {check['id']} crossed")
        result["variants"].append(report)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    cal = subs.add_parser("calibrate")
    cal.add_argument("--pixel-span", type=float)
    cal.add_argument("--length-m", type=float)
    cal.add_argument("--dpi", type=float)
    cal.add_argument("--denominator", type=float)
    cal.add_argument("--image-factor", type=float, default=1)
    check = subs.add_parser("audit")
    check.add_argument("model", type=Path)
    check.add_argument("--strict", action="store_true", help="Exit 1 if any reported issue exists.")
    args = parser.parse_args()
    try:
        if args.command == "calibrate":
            result = calibration(pixel_span=args.pixel_span, length_m=args.length_m,
                                 dpi=args.dpi, denominator=args.denominator,
                                 image_factor=args.image_factor)
        else:
            result = audit(json.loads(args.model.read_text()))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if args.command == "audit" and args.strict and result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
