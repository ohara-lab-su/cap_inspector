# API利用ガイド

本ページはAPIを機能単位で説明します。メソッドの完全なシグネチャとdocstringは[自動生成APIリファレンス](api/modules.html)に掲載します。

## 検査のライフサイクル

`CapInspector` は、カメラと最後に認識したフレームの状態を保持します。`inspect(current_mode=None)` が新しいフレームを読み込み、`process_frame(frame, current_mode=None)` が画像認識を実行します。`current_mode` を指定するとその検査モードに切り替わり、省略すると現在のモードを使用します。モードは `"closed"` または `"opened"` です（互換入力 `"open"` は `"opened"` に正規化）。

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    closed_pass = inspector.inspect("closed")
    status = inspector.get_status()
    print(closed_pass, status)
finally:
    inspector.release()
```

`inspect()` は検査結果を返すと同時に直近の状態を更新します。`is_open()`、`is_closed()`、`is_safe()`、`get_status()` は**読み取り専用**です。これらを連続して呼んでも新しい画像は取得されません。新しい判定が必要な場合は、明示的にもう一度 `inspect()` を呼びます。

## モードと観測状態を区別する

`"closed"` は「閉栓を合格条件とする検査」、`"opened"` は「開栓を合格条件とする検査」です。キャップの観測状態そのものを表す引数ではありません。同じ画像から開栓・閉栓の両条件を評価してフラグを保持するため、閉栓モードで検査した後でも `is_open()` を参照できます。

| 呼び出し | 撮影・認識 | 意味 |
|---|---|---|
| `inspect("closed")` | あり | 閉栓条件で検査する |
| `inspect("opened")` | あり | 開栓条件で検査する |
| `is_closed()` | なし | 最後の画像が閉栓条件を満たしたか |
| `is_open()` | なし | 最後の画像が開栓条件を満たしたか |
| `is_safe()` | なし | 最後の指定モードの検査結果 |
| `get_status()` | なし | `is_safe`, `reason`, `is_open`, `is_closed` の辞書 |

未検査・検出失敗・検査不合格は運用上区別する必要があります。`is_open()` / `is_closed()` が `False` であることだけをもって反対側の状態を確定しないでください。`get_status()` と検出情報も確認します。

## 外部画像を検査する

`process_frame(frame, current_mode=None)` はOpenCVのBGR画像を直接処理します。既存の画像取得系やテスト画像を使う場合はこちらを利用します。`inspect()` と異なり、このメソッド自身はカメラから新しい画像を取得しません。

```python
import cv2
from cap_inspector import CapInspector

frame = cv2.imread("inspection.png")
if frame is None:
    raise RuntimeError("inspection.png could not be read")
inspector = CapInspector()
result = inspector.process_frame(frame, "closed")
print(result, inspector.get_status(), inspector.get_lift_mm())
```

## 検出結果と幾何情報

- `get_detection()` は最後の代表候補の辞書を返します。候補がなければ `None` です。
- `get_detections()` は検出候補の一覧を返します。複数の候補がある場合、代表状態は最後の候補に対応します。
- `get_lift_mm()` は最後に保持したキャップの浮き量（mm）を返します。検出されていない場合は `None` です。
- `get_bottom_points()` はキャップ底面を構成する2点、`get_box_shape()` は回転矩形の頂点情報を返します。

位置情報は画像座標系であり、`BOTTLE_RIM_Y` も画像上のY座標です。カメラ位置を変えると同じ数値が同じ実位置を指すとは限りません。

## 設定API

`get_parameters()` で現在値を取得し、`set_parameters({...})` で指定キーだけを更新します。個別のsetterとして `set_camera_id()`、`set_bottle_rim_y()`、`set_mm_to_PIXEL()`、`set_target_close_mm()`、`set_target_open_mm()`、`set_tolerance_mm()`、`set_mode()` があります。

```python
inspector.set_parameters({
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
})
print(inspector.get_parameters())
inspector.save_parameters("parameters.json")
inspector.load_parameters("parameters.json")
```

`MM_TO_PIXEL` は名前のとおり**px/mm**です。距離計算では画素差をこの値で割ります。`TARGET_CLOSE_MM` と `TARGET_OPEN_MM` は合否判定の中心値であり、片側閾値ではありません。

## カメラと画像ストリーム

`start_camera()` はカメラを開き、`stop_camera()` / `release()` は解放します。`inspect()` は必要に応じてカメラを開始します。`get_image(jpeg_quality=85)` はJPEG画像を取得し、`image_stream(jpeg_quality=85, interval_sec=0.1)` は画像を継続配信します。画像ストリームの取得は状態フラグの読み取りと異なる操作です。

## gRPCクライアント

`CapInspectorClient` は `grpc_frame.grpc_client.GrpcClient` を継承し、サーバー側の公開メソッドを動的に利用します。`image_stream()` はストリーミングRPCを使用します。`CapInspectorClient.save_parameters()` は**クライアント側**のJSONファイルにサーバーの現在値を保存し、`load_parameters()` はクライアント側JSONを読み取ってサーバーに反映します。ローカル `CapInspector` のファイル操作とは実行場所が異なる点に注意してください。

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
try:
    print(client.inspect("closed"))
    print(client.get_status())
    client.save_parameters("remote_parameters.json")
finally:
    client.close()
```

`client.pyi` は開発・配布側が `server_grpc/make_pyi.py` で生成し、配布物に含めます。利用者による生成は不要です。
