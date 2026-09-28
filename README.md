# cap_inspector

既存の `CapInspector` の画像認識処理を維持しながら、`grpc_frame` 経由で認識結果・画像・認識パラメータを扱うための初期実装です。

## 追加した公開 API

- `get_parameters()`
- `set_parameters(parameters)`
- `get_status()`
- `get_image(jpeg_quality=85)`
- `image_stream(jpeg_quality=85, interval_sec=0.1)`

`run()` と `process_frame()` は従来のテスト用途を維持しています。

## サーバ

`examples/server_example.py` は同一の `CapInspector` インスタンスを `ctrl_obj` と `stream_obj` の両方に渡します。

## GUI

`tools/gui_client.py` は `image_stream` を表示しながら、現在の ROI と認識パラメータを編集して `set_parameters()` で反映します。

## GUI ROI selection

The GUI supports both numeric ROI entry and direct ROI selection on the live image.
Drag from one corner of the desired region to the opposite corner. The GUI converts
the selected image coordinates to normalized `roi_x_range` / `roi_y_range`, updates
the parameter fields, and applies them to the server.

## Client class

Application code should use `CapInspectorClient` rather than instantiate grpc_frame's
`GrpcClient` directly:

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
print(client.get_status())
```

`CapInspectorClient` inherits `GrpcClient`, so grpc_frame's dynamically exposed server
methods remain available while the client identity stays explicit.
