# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-ja-blue)](README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

A Python package for detecting red bottle caps with OpenCV and determining whether a cap is open or closed from its position and tilt. It supports local camera inspection as well as remote control and image streaming through `grpc_frame`.

[日本語 README](README.ja.md) | [English documentation](https://ohara-lab-su.github.io/cap_inspector/en/index.html) | [Changelog](CHANGELOG.md)

## Features

- Red-cap detection using two hue ranges in HSV color space.
- Tilt, aspect-ratio, and bottom-edge measurements based on rotated contour rectangles.
- Open/closed inspection using the cap's vertical displacement relative to a bottle-rim reference line.
- Inspection through `inspect(mode)` and retrieval of the latest result through `is_open()` and `is_closed()`.
- Runtime parameter updates and JSON-based configuration persistence.
- Remote inspection, image retrieval and streaming, and a GUI viewer over gRPC.

## Installation

From the project root:

```bash
pip install .
```

For development, `pip install -e .` is also supported. The dependency distribution names are `grpc-frame` and `xlogger-py` (imported in Python as `grpc_frame` and `x_logger`). The GUI uses PySide6.

## Quick start

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    result = inspector.inspect("closed")
    print(result)
    print(inspector.is_closed())
    print(inspector.is_open())
finally:
    inspector.release()
```

Use `inspect("closed")` to check the closed condition or `inspect("opened")` to check the open condition. Both states are evaluated from the same frame. `is_open()` and `is_closed()` return the latest inspection flags without capturing or processing another frame.

## gRPC server and GUI

Start the server:

```bash
python examples/server_example.py
```

Start the GUI client in another terminal:

```bash
python examples/gui_client.py
```

Configure the host and port in the example scripts for your deployment. Additional client and parameter-management examples are available in `examples/`.

## Inspection method

Version 0.1.0 detects red caps across the full frame and measures the cap-bottom displacement from a configured bottle-rim line. Open and closed target displacements and tolerances can be configured independently. Set `BOTTLE_RIM_Y` and `MM_TO_PIXEL` to match the camera geometry.

Version 0.0.0 instead detected white caps within an ROI and compared them with a calibrated closed-cap reference. **The versions differ in both their detection target and inspection algorithm.** See the [technical documentation](https://ohara-lab-su.github.io/cap_inspector/en/index.html) for the detailed comparison and the [changelog](CHANGELOG.md) for release history.

## Documentation

- [English documentation](https://ohara-lab-su.github.io/cap_inspector/en/index.html)
- [API reference](https://ohara-lab-su.github.io/cap_inspector/en/api.html)
- [Examples](https://ohara-lab-su.github.io/cap_inspector/en/examples.html)
- [Changelog](CHANGELOG.md)

The `client.pyi` type stub is generated and packaged by the project maintainer. End users do not need to generate it.

## License

Apache License 2.0. See [LICENSE](LICENSE).
