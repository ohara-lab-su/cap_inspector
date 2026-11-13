# 使用例

実行用スクリプトは `examples/` にあります。使用前に各スクリプトの `HOST`、`PORT`、カメラ設定を環境に合わせて変更してください。

## ローカル検査

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## gRPCサーバーとクライアント

カメラ側で `python examples/server_example.py`、クライアント側で `python examples/client_example.py` を実行します。`CapInspectorClient` から遠隔検査と状態取得を利用できます。

## GUI

サーバー起動後に `python examples/gui_client.py` を実行します。これは運用用の遠隔ビューアーです。ローカルビューアーと `CapInspector.run()` はテスト用です。

## パラメータ管理

`examples/parameter_client.py` はJSON設定の同期、`examples/set_parameters_client.py` は個別・一括設定を示します。設定例は `examples/cap_inspector_parameters.json` を参照してください。

## Local inspection / ローカル検査

```python
from cap_inspector import CapInspector

inspector = CapInspector(camera_id=0, current_mode="closed")
try:
    result = inspector.inspect("closed")
    print(result, inspector.get_status())
    print(inspector.get_lift_mm())
finally:
    inspector.release()
```

## Remote inspection / 遠隔検査

Start `python examples/server_example.py` on the camera computer, then use the following client after setting the server address. / カメラ側でサーバーを起動し、接続先を指定します。

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
try:
    client.start_camera()
    result = client.inspect("opened")
    print(result, client.is_open(), client.get_status())
finally:
    client.stop_camera()
    client.close()
```

## Configuration / 設定

```python
client.set_parameters({
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
})
print(client.get_parameters())
client.save_parameters("cap_inspector_parameters.json")
```

## Remote viewer / 遠隔ビューアー

```bash
python examples/gui_client.py
```

The example scripts define the server address and configuration at the top of each file. / 各スクリプトの冒頭でサーバーアドレスと設定値を指定します。
