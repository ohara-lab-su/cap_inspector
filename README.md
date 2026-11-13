# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-ja-blue)](README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

Python package for red-cap position inspection using OpenCV, with a gRPC client/server powered by `grpc_frame`.

日本語: [README.ja.md](README.ja.md) · [English documentation](docs/en/index.md) · [日本語ドキュメント](docs/ja/index.md)

## Features

- HSV red-region segmentation, contour geometry, cap tilt and height inspection.
- `inspect(mode)` captures one frame, evaluates both open/closed conditions, and returns the selected mode's boolean result.
- `is_open()`, `is_closed()`, `is_safe()` and `get_status()` read the most recent inspection state **without capturing another frame**.
- Runtime parameter updates, JPEG image retrieval, image streaming and remote GUI over `grpc_frame`.
- `run()` is the local camera test; `examples/gui_client.py` is the operational remote viewer.

## Installation

```bash
pip install -e .
```

The distribution names are `grpc-frame` and `xlogger-py` (imported as `grpc_frame` and `x_logger`). GUI requires PySide6.

## Example

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    result = inspector.inspect("closed")
    print(result, inspector.is_closed(), inspector.is_open())
    inspector.set_target_open_mm(3.5)
    inspector.set_parameters({"BOTTLE_RIM_Y": 275, "MM_TO_PIXEL": 4.0})
finally:
    inspector.release()
```

Run the server with `python examples/server_example.py` and the remote GUI with `python examples/gui_client.py`. Configure HOST and PORT in each script. For client-side JSON parameter management see `examples/parameter_client.py` and `examples/set_parameters_client.py`.

## Client type stubs

The package maintainer generates `src/cap_inspector/server_grpc/client.pyi` before building and publishing a release by running `python -m cap_inspector.server_grpc.make_pyi` in the development environment. This command delegates to the existing `grpc_frame.make_pyi` implementation; it does not implement a separate stub generator. The generated `client.pyi` is included in the distributed package so users do not need to generate it.

## Important behavior

`get_image()` and `image_stream()` also process frames and update the shared inspection state. When using concurrent clients, the last processed frame determines the state. `is_open()` and `is_closed()` do not perform additional processing. The inspection thresholds for opened and closed are independent; if their tolerance bands overlap, both flags may be true.

## License

Apache-2.0. See `LICENSE`.
