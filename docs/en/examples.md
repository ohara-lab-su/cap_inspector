# Examples

The `examples/` directory contains executable scripts. Adjust the `HOST`, `PORT` and camera settings in each script before use.

## Local inspection

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## gRPC server and client

Run `python examples/server_example.py` on the camera host and `python examples/client_example.py` on the client. The client uses `CapInspectorClient`, which exposes remote inspection and state queries.

## GUI

Run `python examples/gui_client.py` after starting the server. This is the remote operational viewer. The local viewer and `CapInspector.run()` are for testing.

## Parameters

`examples/parameter_client.py` demonstrates JSON synchronization, while `examples/set_parameters_client.py` demonstrates individual and bulk parameter updates. See `examples/cap_inspector_parameters.json` for a configuration sample.
