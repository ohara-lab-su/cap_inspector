# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

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

## Operation

The gRPC client viewer is provided in `examples/gui_client.py`. The local viewer and `run()` support testing. Configuration can be updated using `set_parameters()` or the individual setters and saved to JSON.

## Further information

- [API](https://ohara-lab-su.github.io/cap_inspector/en/api.html)
- [Examples](https://ohara-lab-su.github.io/cap_inspector/en/examples.html)

```{toctree}
:maxdepth: 2
:caption: Contents

api
examples
```
