# Changelog

[English](CHANGELOG.md) | [日本語](CHANGELOG.ja.md)

## 0.1.0

### Changed

- Refined the recognition pipeline around explicit geometric, tilt, bottom-edge, and lift criteria to improve inspection stability and reproducibility and reduce lighting-related recognition errors; the goal is not merely to detect a different cap color.

- Replaced white-cap segmentation (low saturation and high value in HSV) with two-range red segmentation.
- Replaced the upper-center ROI and largest-candidate selection with full-frame processing of all external contours above the area threshold.
- Changed morphological processing from a 3 × 3 close–open sequence to a 5 × 5 open–close sequence.
- Changed cap geometry measurements to use the rotated minimum-area rectangle, including its tilt, aspect ratio, and bottom edge.
- Replaced the calibrated closed-cap reference with a configured bottle-rim line and fixed pixel-to-millimeter conversion.
- Changed open inspection from a one-sided displacement threshold (at least 5 mm above the calibrated closed position) to a target-and-tolerance check (default 3.5 ± 1.0 mm). Closed inspection uses a 0.5 ± 1.0 mm target. Both checks also require valid cap geometry.
- Centralized image acquisition and inspection in `inspect(mode)`; `is_open()` and `is_closed()` now read the latest inspection flags without acquiring another image.
- Removed the reference-cap calibration procedure from the inspection API.

### Added

- gRPC server and client integration, image retrieval and streaming, and local and remote GUI viewers.
- Runtime parameter update methods and JSON configuration persistence.
- English and Japanese documentation and examples for local and remote operation.

## 0.0.0

### Initial implementation

- Implemented white-cap detection within a configurable region of interest using HSV segmentation, morphology, and contour filtering.
- Added reference-cap calibration for position, dimensions, and angle, with pixel-to-millimeter conversion derived from the cap width.
- Added open and closed inspection against the calibrated reference, including angle and size checks for closed caps.
- Added camera access, status reporting, parameter management, and image streaming.
