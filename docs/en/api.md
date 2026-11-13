# API and configuration

`CapInspector.inspect(mode)` performs frame acquisition and recognition, updates the latest state, and returns a boolean for the selected mode. `is_open()`, `is_closed()`, `is_safe()` and `get_status()` query the stored state without reprocessing.

`get_image()` and `image_stream()` provide image access. The server exposes public methods through `grpc_frame`; no per-method gRPC service implementation is required.

Use `get_parameters()` to read settings, `set_parameters()` to update a subset, or individual setters (`set_camera_id`, `set_bottle_rim_y`, `set_mm_to_PIXEL`, `set_target_close_mm`, `set_target_open_mm`, `set_tolerance_mm`, `set_mode`). The initial settings may be supplied to the constructor. `save_parameters()` and `load_parameters()` support JSON-based configuration.

Before packaging a release, the package maintainer runs `python -m cap_inspector.server_grpc.make_pyi` in the development environment. The entry point delegates to `grpc_frame.make_pyi` and generates `src/cap_inspector/server_grpc/client.pyi`. The generated stub is included in the distribution; end users do not generate it.
