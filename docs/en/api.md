# API and configuration

`CapInspector.inspect(mode)` performs frame acquisition and recognition, updates the latest state, and returns a boolean for the selected mode. `is_open()`, `is_closed()`, `is_safe()` and `get_status()` query the stored state without reprocessing.

`get_image()` and `image_stream()` provide image access. The server exposes public methods through `grpc_frame`; no per-method gRPC service implementation is required.

Use `get_parameters()` to read settings, `set_parameters()` to update a subset, or individual setters (`set_camera_id`, `set_bottle_rim_y`, `set_mm_to_PIXEL`, `set_target_close_mm`, `set_target_open_mm`, `set_tolerance_mm`, `set_mode`). The initial settings may be supplied to the constructor. `save_parameters()` and `load_parameters()` support JSON-based configuration.

Before packaging a release, the package maintainer runs `python -m cap_inspector.server_grpc.make_pyi` in the development environment. The entry point delegates to `grpc_frame.make_pyi` and generates `src/cap_inspector/server_grpc/client.pyi`. The generated stub is included in the distribution; end users do not generate it.

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

