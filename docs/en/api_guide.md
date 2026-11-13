# API usage guide

This page explains API behavior and operational contracts. For complete signatures and docstrings, see the [generated API reference](api/modules.html).

## Inspection lifecycle

`CapInspector` owns the camera and the most recently inspected frame state. `inspect(current_mode=None)` acquires a frame and performs inspection through `process_frame(frame, current_mode=None)`. A supplied mode changes the active inspection mode; otherwise the current mode is used. Supported modes are `"closed"` and `"opened"` (`"open"` is accepted as a compatibility alias).

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    closed_pass = inspector.inspect("closed")
    status = inspector.get_status()
    print(closed_pass, status)
finally:
    inspector.release()
```

`inspect()` returns the selected-mode result and updates cached state. `is_open()`, `is_closed()`, `is_safe()`, and `get_status()` are **read-only queries**. Calling them does not acquire or classify another frame. Call `inspect()` explicitly for a new observation.

## Inspection mode versus observed state

`"closed"` means *test against the closed acceptance condition*; `"opened"` means *test against the open acceptance condition*. They are not direct declarations of observed state. Both conditions are evaluated on the same frame, so `is_open()` remains meaningful after `inspect("closed")`.

| Call | New acquisition | Meaning |
|---|---|---|
| `inspect("closed")` | Yes | Inspect against the closed condition |
| `inspect("opened")` | Yes | Inspect against the open condition |
| `is_closed()` | No | Read the last closed-condition flag |
| `is_open()` | No | Read the last open-condition flag |
| `is_safe()` | No | Read the last selected-mode result |
| `get_status()` | No | Read `is_safe`, `reason`, `is_open`, `is_closed` |

Do not infer that a cap is open solely because `is_closed()` returns `False`, or vice versa. A failed detection or uninitialized state must be considered; inspect `get_status()` and the detection data.

## Inspect an existing image

`process_frame(frame, current_mode=None)` accepts an OpenCV BGR image and does not capture a new camera frame itself.

```python
import cv2
from cap_inspector import CapInspector

frame = cv2.imread("inspection.png")
if frame is None:
    raise RuntimeError("inspection.png could not be read")
inspector = CapInspector()
result = inspector.process_frame(frame, "closed")
print(result, inspector.get_status(), inspector.get_lift_mm())
```

## Detection geometry

- `get_detection()` returns the last representative candidate dictionary, or `None` when none exists.
- `get_detections()` returns the candidate list; with multiple candidates, the last one is currently retained as the representative state.
- `get_lift_mm()` returns the last lift in millimeters, or `None` if unavailable.
- `get_bottom_points()` returns the two cap-bottom points; `get_box_shape()` returns the rotated-rectangle vertices.

The geometric coordinates are image coordinates. Repositioning the camera may invalidate `BOTTLE_RIM_Y` and the pixel-to-distance conversion.

## Configuration API

Use `get_parameters()` to inspect current settings and `set_parameters({...})` to update selected keys. Individual setters include `set_camera_id()`, `set_bottle_rim_y()`, `set_mm_to_PIXEL()`, `set_target_close_mm()`, `set_target_open_mm()`, `set_tolerance_mm()`, and `set_mode()`.

```python
inspector.set_parameters({
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
})
print(inspector.get_parameters())
inspector.save_parameters("parameters.json")
inspector.load_parameters("parameters.json")
```

`MM_TO_PIXEL` is measured in **pixels per millimeter**. The lift formula divides pixel distance by this value. Open and closed targets are centers of tolerance intervals, not one-sided thresholds.

## Camera and image streaming

`start_camera()` opens the camera; `stop_camera()` and `release()` release it. `inspect()` starts it when necessary. `get_image(jpeg_quality=85)` obtains JPEG image data and `image_stream(jpeg_quality=85, interval_sec=0.1)` provides a continuous stream. Streaming image acquisition is distinct from reading cached inspection flags.

## gRPC client

`CapInspectorClient` inherits `grpc_frame.grpc_client.GrpcClient` and uses dynamically exposed server methods. `image_stream()` uses streaming RPC. `CapInspectorClient.save_parameters()` writes current server settings to a **client-side** JSON file; `load_parameters()` reads client-side JSON and applies it to the server. This differs from the execution location of local `CapInspector` file operations.

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
try:
    print(client.inspect("closed"))
    print(client.get_status())
    client.save_parameters("remote_parameters.json")
finally:
    client.close()
```

The `client.pyi` type stub is generated by the maintainer using `server_grpc/make_pyi.py` and included in the distributed package. Users do not generate it.
