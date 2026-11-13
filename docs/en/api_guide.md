# API guide (manual)

This page explains how the public interfaces fit together. For method signatures and docstrings, see the [automatically generated Python API](api/modules.html).

## Inspection and state

`CapInspector.inspect(current_mode=None)` acquires a camera frame and evaluates the configured mode. `process_frame(frame, current_mode=None)` evaluates an existing BGR frame. Both update the most recent inspection state. `is_open()` and `is_closed()` only read the stored flags. `is_safe()` returns the most recent selected-mode result, and `get_status()` returns a dictionary containing `is_safe`, `reason`, `is_open` and `is_closed`.

## Geometry and diagnostics

`get_detection()` returns the representative detection, `get_detections()` all qualifying detections, and `get_lift_mm()`, `get_bottom_points()` and `get_box_shape()` expose the last geometry measurement. The reference line and pixel scale can be queried and updated with the corresponding getters and setters.

## Camera and streaming

`start_camera()` and `stop_camera()` manage capture; `release()` releases the camera. `get_image()` provides a JPEG image and `image_stream()` supplies a sequence of images for remote viewers.

## Remote interface

`cap_inspector.server_grpc.CapInspectorClient` derives from `grpc_frame.grpc_client.GrpcClient`. The server exposes the device methods through `grpc_frame`; `image_stream()` uses streaming RPC. The client-side `save_parameters()` and `load_parameters()` write/read local JSON files while synchronizing the server settings. The gRPC client type stub is generated and shipped by package maintainers; end users do not generate it.
