# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-ja-blue)](README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

Python package for red-cap position inspection using OpenCV, with a gRPC client/server powered by `grpc_frame`.

日本語: [README.ja.md](README.ja.md) · [English documentation](docs/en/index.md) · [日本語ドキュメント](docs/ja/index.md)

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


## Features

- HSV red-region segmentation, contour geometry, cap tilt and height inspection.
- `inspect(mode)` captures one frame, evaluates both open/closed conditions, and returns the selected mode's boolean result.
- `is_open()`, `is_closed()`, `is_safe()` and `get_status()` read the most recent inspection state **without capturing another frame**.
- Runtime parameter updates, JPEG image retrieval, image streaming and remote GUI over `grpc_frame`.
- `run()` is the local camera test; `examples/gui_client.py` is the operational remote viewer.

## Installation

```bash
pip install -e .
```

The distribution names are `grpc-frame` and `xlogger-py` (imported as `grpc_frame` and `x_logger`). GUI requires PySide6.

## Example

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    result = inspector.inspect("closed")
    print(result, inspector.is_closed(), inspector.is_open())
    inspector.set_target_open_mm(3.5)
    inspector.set_parameters({"BOTTLE_RIM_Y": 275, "MM_TO_PIXEL": 4.0})
finally:
    inspector.release()
```

Run the server with `python examples/server_example.py` and the remote GUI with `python examples/gui_client.py`. Configure HOST and PORT in each script. For client-side JSON parameter management see `examples/parameter_client.py` and `examples/set_parameters_client.py`.

## Client type stubs

The package maintainer generates `src/cap_inspector/server_grpc/client.pyi` before building and publishing a release by running `python -m cap_inspector.server_grpc.make_pyi` in the development environment. This command delegates to the existing `grpc_frame.make_pyi` implementation; it does not implement a separate stub generator. The generated `client.pyi` is included in the distributed package so users do not need to generate it.

## Important behavior

`get_image()` and `image_stream()` also process frames and update the shared inspection state. When using concurrent clients, the last processed frame determines the state. `is_open()` and `is_closed()` do not perform additional processing. The inspection thresholds for opened and closed are independent; if their tolerance bands overlap, both flags may be true.

## License

Apache-2.0. See `LICENSE`.
