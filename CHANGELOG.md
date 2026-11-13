# Changelog

## 0.1.0

- Migrated red-cap detection from `camera9_2.py` to the `CapInspector` class.
- Added per-frame open and closed flags; `is_open()` and `is_closed()` now read the latest inspection state without triggering a new capture.
- Kept `inspect()` as the frame-acquisition and inspection entry point.
- Provided parameter setters, JSON configuration, gRPC client/server, local and remote viewers.
- Added Japanese and English README and documentation, and `grpc_frame`-based `.pyi` generation entry point.
