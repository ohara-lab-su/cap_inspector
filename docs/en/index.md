# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCV-based inspection of red caps, available locally or through `grpc_frame`.

## Image-recognition algorithm: v0.0.0 vs v0.1.0

**This is not merely an ROI change.** The target color, candidate selection, geometry, distance reference, and open/closed criteria have all changed.

| Stage | v0.0.0 (supplied original core) | v0.1.0 (`camera9_2.py`-based) |
|---|---|---|
| Search region | Fractional ROI near the upper center (defaults: x 30–70%, y 0–35%) | Entire frame; no ROI cropping |
| Color segmentation | **White**, using low-saturation/high-value HSV (default H 0–180, S 0–30, V 170–255) | **Red**, using two HSV hue bands (H 0–10 and 170–180; S 120–255, V 70–255), combined into one mask |
| Morphology | 3×3 kernel; close then open | 5×5 kernel; open then close |
| Contour selection | Area ≥800, near ROI center; exclude near-full-ROI regions; select largest remaining candidate | Process **all** external contours with area >500; no largest-candidate selection |
| Geometry | Axis-aligned `boundingRect` for size and bottom; `minAreaRect` for angle | Rotated `minAreaRect` for tilt, aspect ratio, and bottom edge |
| Tilt criterion | Difference from the calibrated reference angle | Tilt <3° from horizontal and width/height ratio 2.3–2.8 |
| Position reference | Bottom of a correctly closed cap captured using `calibrate()` | Configured bottle-rim line `BOTTLE_RIM_Y` (default 275 px) |
| Pixel-to-mm conversion | Calibrated physical cap width (default 30 mm) divided by observed width | Fixed `MM_TO_PIXEL` scale (default 4 px/mm) |
| Closed criterion | Bottom within ±1 mm of calibrated reference, with angle difference and width/height differences (defaults ≤25%) checked | Lift 0.5±1.0 mm from bottle-rim line, plus tilt/aspect-ratio checks |
| Open criterion | Upward movement **at least 5 mm** from calibrated closed reference, plus angle check | Lift 3.5±1.0 mm from bottle-rim line, plus tilt/aspect-ratio checks |
| State API | `is_open()` / `is_closed()` also capture and reprocess frames while temporarily changing mode | `inspect(mode)` captures, evaluates both conditions and updates state; `is_open()` / `is_closed()` only read cached flags |

In v0.1.0, `lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL`. The bottom coordinate is the mean Y coordinate of the two lowest vertices of the rotated rectangle. Both open and closed checks use an **absolute deviation from a target**. This differs fundamentally from v0.0.0's one-sided open threshold of at least 5 mm.

**Migration implications:** White-cap detection and reference-cap calibration do not carry over. Configure `BOTTLE_RIM_Y`, `MM_TO_PIXEL`, target lifts, and tolerance for the imaging setup. The v0.0.0 comparison against calibrated cap width/height is replaced by a rotated-rectangle aspect-ratio test, which is not equivalent. v0.1.0 processes every qualifying contour; its cached representative status corresponds to the last processed contour.


## Operation

`inspect(mode)` captures and processes one frame. The mode selects the returned boolean result (`opened` or `closed`); both state flags are evaluated from that frame. `is_open()`, `is_closed()` and `get_status()` read the last result without acquiring another image.

The remote viewer in `examples/gui_client.py` is intended for operation. `run()` and the local viewer are for testing.

## Parameters

Constructor arguments are initial values. Use individual `set_xxx()` methods or `set_parameters()` to update values during operation. `BOTTLE_RIM_Y` and `MM_TO_PIXEL` replace the former ROI-based calibration approach. See `examples/set_parameters_client.py` for both individual and batch updates.

## Usage

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## Documentation

- [English API and usage](api.md)
- [English examples](examples.md)
- [日本語](../ja/index.html)
