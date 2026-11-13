# cap_inspector

キャップの画像認識と開閉状態の判定を行うPythonパッケージです。OpenCVによる画像処理を使用し、ローカルでの動作確認と、`grpc_frame` を介した遠隔操作に対応します。

## 機能

- カメラ画像から赤色領域を抽出し、キャップの輪郭・傾斜・形状・底面位置を解析
- 瓶の基準線に対するキャップ位置から開閉状態を判定
- `inspect()` による1フレームの真偽判定
- `get_image()` と `image_stream()` による画像取得
- パラメータの個別変更、一括変更、JSONへの保存・読込
- ローカルビューアーおよびgRPCクライアントビューアー

## ディレクトリ構成

```text
src/cap_inspector/
    __init__.py
    cap_inspector.py
    viewer.py
    server_grpc/
        __init__.py
        client.py
        make_pyi.py
        server.py
examples/
    cap_inspector_parameters.json
    client_example.py
    gui_client.py
    parameter_client.py
    roi_client.py
    server_example.py
    set_parameters_client.py
```

## 基本的な使い方

```python
from cap_inspector import CapInspector

inspector = CapInspector(
    camera_id=0,
    BOTTLE_RIM_Y=275,
    MM_TO_PIXEL=4.0,
    TARGET_CLOSE_MM=0.5,
    TARGET_OPEN_MM=3.5,
    TOLERANCE_MM=1.0,
    current_mode="closed",
)

try:
    inspector.start_camera()
    is_closed = inspector.inspect()
    print(is_closed)
    print(inspector.get_status())
finally:
    inspector.release()
```

コンストラクタ引数は初期値です。運用中は `set_parameters()` または個別の `set_xxx()` メソッドで変更できます。

```python
inspector.set_bottle_rim_y(280)
inspector.set_target_open_mm(3.5)
inspector.set_mode("opened")
inspector.set_parameters({"MM_TO_PIXEL": 4.0, "TOLERANCE_MM": 1.0})
```

設定の詳細は `examples/set_parameters_client.py` と `examples/parameter_client.py` を参照してください。

## gRPCサーバー・クライアント

`grpc_frame` を使用して画像認識クラスの公開メソッドを遠隔呼び出しできます。サーバーとクライアントの起動例は次のファイルです。

- `examples/server_example.py`：サーバー起動
- `examples/client_example.py`：クライアントからの判定
- `examples/gui_client.py`：gRPC接続によるGUIビューアー（通常運用）
- `src/cap_inspector/viewer.py`：ローカル／gRPC共通の表示処理

接続先や画像取得間隔などは各サンプル内の設定値を変更してください。

## 型スタブ

クライアントの型スタブは、`grpc_frame` に含まれる生成機能を利用します。`grpc_frame` がインストールされた環境で、プロジェクトルートから実行してください。

```bash
python src/cap_inspector/server_grpc/make_pyi.py
```

生成先は `src/cap_inspector/server_grpc/client.pyi` です。

## 判定パラメータ

- `BOTTLE_RIM_Y`：瓶の基準線の画像上のY座標
- `MM_TO_PIXEL`：距離換算係数
- `TARGET_CLOSE_MM`：閉栓判定の目標位置
- `TARGET_OPEN_MM`：開栓判定の目標位置
- `TOLERANCE_MM`：位置判定の許容差
- `current_mode`：判定対象の状態（`closed` / `opened`）

旧方式のROIによる検出範囲指定や `calibrate()` は使用しません。基準線・換算係数はパラメータとして設定します。

## 動作確認

`CapInspector.run()` は、カメラ画像の認識結果をローカル表示するテスト用ルーチンです。通常の遠隔操作にはgRPCクライアントを使用してください。
