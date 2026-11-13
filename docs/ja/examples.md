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
