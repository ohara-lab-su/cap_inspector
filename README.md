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
