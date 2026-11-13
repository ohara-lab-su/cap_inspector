# cap_inspector

[English](README.md) | [日本語](README.ja.md) | [Documentation](https://ohara-lab-su.github.io/cap_inspector/en/index.html) | [GitHub](https://github.com/ohara-lab-su/cap_inspector)

An OpenCV-based package for inspecting whether bottle caps are open or closed. Its primary goal is **more stable and reproducible inspection through a better-defined recognition algorithm and explicit acceptance criteria**, not a change in cap color. To reduce missed detections and false positives caused by lighting variations, the inspection evaluates candidate regions using geometry, tilt, and bottom-edge position, then applies numerical lift criteria. The project covers black as well as red caps. It supports local camera inspection, JSON configuration, gRPC remote control and image streaming, and a GUI viewer.

## Image recognition and inspection

The current red-cap detection configuration uses the following processing steps. Color segmentation depends on the target: the same HSV thresholds must not be assumed to work for black caps. This does not guarantee invariance to lighting; imaging conditions and detection settings must still be matched.

1. Convert the camera frame to HSV and combine masks for the two red hue ranges (H 0–10 and 170–180; S 120–255, V 70–255).
2. Apply morphological opening followed by closing with a 5 × 5 kernel. Extract external contours and examine contours with an area greater than 500 pixels².
3. Fit a rotated minimum-area rectangle to each contour. Check that the tilt is less than 3° and the width-to-height ratio is between 2.3 and 2.8.
4. Determine the cap bottom from the two lowest rectangle vertices. Calculate its lift relative to the configured bottle-rim line:

   `lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL`

5. Compare the lift with the closed and open targets independently. The defaults are 0.5 mm (closed) and 3.5 mm (open), with a ±1.0 mm tolerance for each.

The reference line and pixel scale depend on the camera installation and must be configured for the measurement geometry. The detector examines all qualifying contours; the current representative state corresponds to the last processed qualifying contour. A frame with no detected cap does not pass inspection.

`inspect(mode)` captures and processes a frame, updates both state flags, and returns the result for `"closed"` or `"opened"`. `is_closed()` and `is_open()` only return the latest stored flags; they do not capture another frame. The state is therefore associated with the most recent inspection, not a continuous measurement.

## Installation

```bash
pip install .
```

For an editable installation, use `pip install -e .`. The dependency distribution names are `grpc-frame` and `xlogger-py` (Python imports: `grpc_frame` and `x_logger`). The GUI uses PySide6.

## Basic usage

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## gRPC and GUI

Run `python examples/server_example.py` to start the server, then `python examples/gui_client.py` on the client machine. Configure the connection in the example scripts. The remote GUI is the operational viewer; the local viewer and `run()` are intended for testing. See `examples/` for inspection and parameter-setting scripts.

## Documentation

- [API reference](https://ohara-lab-su.github.io/cap_inspector/en/api_guide.html)
- [Examples](https://ohara-lab-su.github.io/cap_inspector/en/examples.html)
- [Generated Python API](https://ohara-lab-su.github.io/cap_inspector/en/api/modules.html)
- [Changelog](CHANGELOG.md)

## License

Apache License 2.0. See [LICENSE](LICENSE).
