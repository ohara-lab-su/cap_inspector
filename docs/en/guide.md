# User guide

## Purpose and operating conditions

The inspection algorithm aims to improve stability and repeatability by combining candidate segmentation with geometric validation and explicit cap-lift thresholds. A fixed camera viewpoint and a configured bottle-rim reference are required. This is not an illumination-invariant detector; thresholds and lighting must be validated for each installation. Although the project also addresses black caps, the present `_detect_cap()` implementation segments **red** regions only. Black-cap detection must not be assumed to be implemented by the red HSV thresholds.

## Recognition pipeline

1. Convert the BGR image to HSV; combine the red ranges H=0–10 and H=170–180 (S=120–255, V=70–255).
2. Apply morphological opening and closing with a 5×5 kernel, then extract external contours. Ignore contours with an area of 500 pixels² or less.
3. Fit `cv2.minAreaRect()` to each remaining contour; require a tilt under 3° and a width/height ratio between 2.3 and 2.8.
4. Find the two lowest vertices of the rotated rectangle and average their vertical coordinates to estimate the cap bottom.
5. Compute `lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL`.
6. Test the closed target (0.5±1.0 mm) and opened target (3.5±1.0 mm) independently, also requiring valid geometry.

These are default parameters, not universal mechanical tolerances. Set the reference line and scale for the camera geometry. The implementation evaluates multiple qualifying contours and stores the last qualifying contour as the representative result; the complete set is available from `get_detections()`.

## Inspection lifecycle

`inspect(mode)` captures one frame and updates both state flags. `is_open()`, `is_closed()`, `is_safe()` and `get_status()` read stored results without capturing another frame. When no qualifying cap is detected, the inspection fails. The mode accepts `closed` and `opened`; the legacy alias `open` is normalized to `opened`.

## Configuration

Use `get_parameters()` to inspect the current settings, `set_parameters({...})` or individual setters to update them, and `save_parameters(path)` / `load_parameters(path)` for JSON persistence. The gRPC client implements file persistence on the **client** machine.
