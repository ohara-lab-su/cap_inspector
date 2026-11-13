# Changelog

English | [日本語](CHANGELOG.ja.md)

This changelog records the changes between the supplied v0.0.0 core implementation and the current v0.1.0 package. The v0.0.0 entry describes the supplied source code; it does not imply a separately verified release date.

## 0.1.0

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


### Changed

- Replaced the v0.0.0 white-cap detection and reference-cap calibration approach with the red-cap detection algorithm based on `camera9_2.py`.
- Changed the inspection criteria to evaluate cap lift relative to a configured bottle-rim position, using the closed/open targets and tolerance.
- Made `inspect(mode)` the image acquisition and inspection entry point. It updates both open and closed results from the same inspection, then returns the result for the requested mode.
- Changed `is_open()` and `is_closed()` to read the latest stored inspection flags without capturing or processing another frame.
- Removed the former reference-cap calibration workflow from the new inspection API.

### Added

- Parameter access and update methods, including individual setters and JSON save/load support.
- Detection-result accessors and image acquisition/streaming interfaces.
- gRPC server and client integration through `grpc_frame`, with local and remote GUI viewer support and usage examples.
- English and Japanese README files and GitHub Pages documentation, plus a root-level `pages.yml` workflow template.
- A maintainer-side entry point for generating the gRPC client type stub (`.pyi`). Stub generation is a packaging responsibility, not an installation step for users.

## 0.0.0

### Initial core implementation

- Implemented the `CapInspector` class with OpenCV camera capture and an ROI-based cap search.
- Detected white cap candidates using HSV thresholding, morphological operations, contour filtering, and geometric checks.
- Evaluated cap angle and position, with optional smoothing across frames.
- Supported closed/open inspection modes, safety/status queries, and a reference-cap calibration procedure.
- Exposed configuration through constructor parameters, parameter getters/setters, and JSON save/load methods.
- Included image capture, JPEG streaming, a local OpenCV test loop, and camera resource management.

The v0.0.0 description is based on the supplied `cap_inspector_v0.0.0(1).py` core source. It does not assert that the later package layout or gRPC integration existed in v0.0.0.
