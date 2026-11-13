# cap_inspector

**English** | [日本語](README.ja.md) | [GitHub](https://github.com/ohara-lab-su/cap_inspector)

**cap_inspector** is a Python package for inspecting whether bottle caps are open or closed using camera images. It combines OpenCV-based inspection, local operation, gRPC remote control and image streaming, and a GUI viewer.

Its principal goal is **stable, reproducible inspection through explicit geometric criteria**, not changing the color of the cap. Candidate regions are assessed by shape, tilt, and position; the cap's lift relative to a bottle reference line is then compared with defined acceptance intervals. This approach aims to reduce failures caused by lighting variation. The project targets applications involving red and black caps, but the color-segmentation implementation currently verified in the code uses HSV thresholds for **red** caps; black-cap segmentation should not be assumed to be implemented.

## Features

- **Image processing:** HSV segmentation, morphological filtering, contours, and rotated-rectangle geometry.
- **Open/closed inspection:** lift measured in millimeters against separate open and closed acceptance intervals.
- **Cached results:** `inspect()` performs acquisition and classification; `is_open()` / `is_closed()` read the latest flags without acquiring another frame.
- **Configuration:** runtime parameter updates and JSON import/export.
- **Remote operation:** inspection, configuration, JPEG streaming via `grpc-frame`, and a PySide6 viewer.

## Installation

From the project root:

```bash
pip install .
```

For development, use `pip install -e .`. The distribution names `grpc-frame` and `xlogger-py` differ from their import names `grpc_frame` and `x_logger`.

## Quick start: local inspection

```python
from cap_inspector import CapInspector

inspector = CapInspector(
    camera_id=0,
    BOTTLE_RIM_Y=275,
    MM_TO_PIXEL=4.0,
    current_mode="closed",
)
try:
    passed = inspector.inspect("closed")
    print("Closed inspection:", passed)
    print("Closed:", inspector.is_closed())
    print("Opened:", inspector.is_open())
    print("Status:", inspector.get_status())
    print("Lift (mm):", inspector.get_lift_mm())
finally:
    inspector.release()
```

Use `inspect("closed")` to test the closed condition and `inspect("opened")` for the open condition. Both update the open and closed flags using the same frame. `is_open()` and `is_closed()` only read the latest inspection result. Use `get_status()` to distinguish unavailable inspection information from a failed acceptance test.

## Recognition and classification algorithm

The current red-cap detection pipeline is:

1. Convert BGR to HSV and combine two red hue ranges (H: 0–10 and 170–180; S: 120–255; V: 70–255).
2. Apply opening followed by closing with a 5×5 kernel to clean the mask.
3. Extract external contours and evaluate those with area above 500 pixels².
4. Fit `minAreaRect` to each candidate and require tilt below 3° and width/height ratio between 2.3 and 2.8.
5. Determine the cap bottom from the two lower rectangle vertices and compute lift from the bottle reference line:

```text
lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL
```

| Parameter | Default | Purpose |
|---|---:|---|
| `BOTTLE_RIM_Y` | 275 px | Bottle reference line in image coordinates |
| `MM_TO_PIXEL` | 4.0 px/mm | Image-to-distance conversion |
| `TARGET_CLOSE_MM` | 0.5 mm | Closed-cap target lift |
| `TARGET_OPEN_MM` | 3.5 mm | Open-cap target lift |
| `TOLERANCE_MM` | 1.0 mm | Acceptance tolerance around each target |

The calculated lift must fall within the respective target ± tolerance. Classification is therefore **not based solely on whether a colored region exists**. Lighting invariance is not guaranteed: thresholds, camera geometry, and the reference line must be appropriate for the installation. The current implementation processes multiple candidates and retains the last candidate as the representative result.

## Runtime configuration

```python
inspector.set_parameters({
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
    "mode": "closed",
})
print(inspector.get_parameters())
inspector.save_parameters("cap_inspector_parameters.json")
inspector.load_parameters("cap_inspector_parameters.json")
```

Recheck `BOTTLE_RIM_Y` and `MM_TO_PIXEL` after changing the camera position or field of view. Changing the inspection mode does not cause status getters to acquire new images.

## gRPC server and remote GUI

Run the server and GUI client in separate terminals, adjusting `HOST` and `PORT` in the example scripts:

```bash
python examples/server_example.py
python examples/gui_client.py
```

The API is also accessible from a Python client:

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
try:
    client.start_camera()
    print(client.inspect("closed"))
    print(client.get_status())
finally:
    client.stop_camera()
    client.close()
```

`examples/client_example.py` demonstrates remote inspection; `examples/parameter_client.py` demonstrates JSON synchronization; `examples/set_parameters_client.py` shows individual setters and bulk updates; and `examples/gui_client.py` launches the remote viewer. The `.pyi` type stub is generated and distributed by the package maintainer, not by end users.

## API quick reference

| API | Purpose |
|---|---|
| `inspect(mode)` | Acquire and classify one frame; return the selected-mode result |
| `process_frame(frame, mode)` | Classify an existing BGR frame |
| `is_open()` / `is_closed()` | Read the latest open/closed flags |
| `is_safe()` / `get_status()` | Read the selected-mode result and detailed status |
| `get_lift_mm()` / `get_detections()` | Read measured lift and candidate data |
| `get_parameters()` / `set_parameters(...)` | Inspect and update configuration |
| `save_parameters(path)` / `load_parameters(path)` | Export and import JSON configuration |
| `get_image()` / `image_stream()` | Obtain JPEG frames or a continuous stream |
| `start_camera()` / `stop_camera()` / `release()` | Manage the camera lifecycle |

## License

Apache License 2.0. See [LICENSE](LICENSE).
