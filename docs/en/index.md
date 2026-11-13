# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCV-based inspection of red caps, available locally or through `grpc_frame`.

## Operation

`inspect(mode)` captures and processes one frame. The mode selects the returned boolean result (`opened` or `closed`); both state flags are evaluated from that frame. `is_open()`, `is_closed()` and `get_status()` read the last result without acquiring another image.

The remote viewer in `examples/gui_client.py` is intended for operation. `run()` and the local viewer are for testing.

## Parameters

Constructor arguments are initial values. Use individual `set_xxx()` methods or `set_parameters()` to update values during operation. `BOTTLE_RIM_Y` and `MM_TO_PIXEL` replace the former ROI-based calibration approach. See `examples/set_parameters_client.py` for both individual and batch updates.

## Usage

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## Documentation

- [English API and usage](api.md)
- [English examples](examples.md)
- [日本語](../ja/index.html)
