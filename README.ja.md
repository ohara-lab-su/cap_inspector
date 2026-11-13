# cap_inspector

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/cap_inspector/blob/main/README.md) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/cap_inspector/blob/main/README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

**cap_inspector** は、カメラ画像からボトルキャップの開閉状態を検査するPythonパッケージです。OpenCVによる画像認識、ローカル検査、gRPCを介した遠隔検査・画像配信、GUIによる状態確認を提供します。

本プロジェクトの中心は、キャップの色を変更することではなく、**検出候補の形状・傾き・位置を組み合わせ、開閉判定の幾何学的基準を明示することで、検査を安定させること**です。照明の変動による認識失敗を抑え、撮影条件と判定条件を管理しやすくします。赤色・黒色キャップを対象とする用途を想定していますが、現在の実装で確認できる色抽出処理は赤色用HSVマスクです。黒色用の検出処理が実装済みであるとは扱いません。

## 主な機能

- **画像認識**：HSVマスク、モルフォロジー処理、輪郭抽出、回転矩形による形状・傾き判定。
- **開閉検査**：キャップ底面と瓶の基準線との距離をmmに換算し、開栓・閉栓それぞれの許容範囲で評価。
- **結果の再利用**：`inspect()` が1回の撮影と判定を実行し、`is_open()` / `is_closed()` はその結果を参照。問い合わせ時に再撮影しません。
- **設定管理**：判定基準、画素換算、カメラ番号を実行中に変更し、JSONに保存・復元。
- **遠隔操作**：`grpc-frame` による検査・パラメータ変更・JPEG画像ストリーム、PySide6ビューアー。

## インストール

プロジェクトのルートで実行します。

```bash
pip install .
```

開発時は `pip install -e .` を利用できます。依存パッケージの配布名 `grpc-frame` / `xlogger-py` と、Pythonのimport名 `grpc_frame` / `x_logger` は異なります。

## クイックスタート：ローカル検査

```python
from cap_inspector import CapInspector

inspector = CapInspector(
    camera_id=0,
    BOTTLE_RIM_Y=275,
    MM_TO_PIXEL=4.0,
    current_mode="closed",
)
try:
    passed = inspector.inspect("closed")
    print("Closed inspection:", passed)
    print("Closed:", inspector.is_closed())
    print("Opened:", inspector.is_open())
    print("Status:", inspector.get_status())
    print("Lift (mm):", inspector.get_lift_mm())
finally:
    inspector.release()
```

`inspect("closed")` は閉栓条件で検査し、`inspect("opened")` は開栓条件で検査します。両者とも認識結果から開栓・閉栓フラグを更新します。`is_open()` と `is_closed()` は直近の検査結果を返すだけで、再判定は行いません。未検査・検出失敗と「条件を満たさない」は `get_status()` などを併せて確認してください。

## 画像認識アルゴリズム

現在の赤色キャップ用の処理は次のとおりです。

1. BGR画像をHSVに変換し、赤色の2つの色相範囲（H: 0–10、170–180、S: 120–255、V: 70–255）を結合します。
2. 5×5カーネルでオープニングとクロージングを実施し、マスクの小さなノイズや欠損を処理します。
3. 外部輪郭を抽出し、面積500 pixel²超の候補を評価します。
4. `minAreaRect` から回転矩形を求め、水平からの傾き3°未満、横縦比2.3–2.8の条件で候補を選別します。
5. 回転矩形の下側2頂点から底面位置を求め、瓶の基準線からの浮き量を算出します。

```text
lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL
```

| 設定値 | 初期値 | 用途 |
|---|---:|---|
| `BOTTLE_RIM_Y` | 275 px | 瓶の基準線（画像Y座標） |
| `MM_TO_PIXEL` | 4.0 px/mm | 画素から実距離への換算 |
| `TARGET_CLOSE_MM` | 0.5 mm | 閉栓時の目標浮き量 |
| `TARGET_OPEN_MM` | 3.5 mm | 開栓時の目標浮き量 |
| `TOLERANCE_MM` | 1.0 mm | 各目標値に対する許容差 |

閉栓・開栓とも、計算した浮き量がそれぞれの目標値の±許容差に入るかを評価します。これは単なる色領域の有無による判定ではありません。**照明条件の変化を完全に補償する方式ではない**ため、HSV閾値とカメラ設置・基準線の整合が必要です。現在の実装では複数候補を処理し、代表状態には最後の候補の結果を保持します。

## 実行中のパラメータ変更

```python
inspector.set_parameters({
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
    "mode": "closed",
})
print(inspector.get_parameters())
inspector.save_parameters("cap_inspector_parameters.json")
inspector.load_parameters("cap_inspector_parameters.json")
```

カメラの位置・画角を変更した場合は `BOTTLE_RIM_Y` と `MM_TO_PIXEL` を再確認してください。モードの変更は検査条件の変更であり、状態取得メソッドによる再検査は発生しません。

## gRPCサーバーと遠隔GUI

サーバーとクライアントを別々の端末で起動します。接続先は各使用例の `HOST` / `PORT` を設定します。

```bash
python examples/server_example.py
python examples/gui_client.py
```

Pythonクライアントからも操作できます。

```python
from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
try:
    client.start_camera()
    print(client.inspect("closed"))
    print(client.get_status())
finally:
    client.stop_camera()
    client.close()
```

`examples/client_example.py` は遠隔検査、`examples/parameter_client.py` はJSONによる設定の送受信、`examples/set_parameters_client.py` は個別setterと一括設定、`examples/gui_client.py` は遠隔GUIを示します。gRPCクライアントの `.pyi` 型スタブは配布側で生成・同梱するもので、利用者による生成は不要です。

## API早見表

| API | 内容 |
|---|---|
| `inspect(mode)` | 1フレームを撮影・認識し、指定モードの検査結果を返す |
| `process_frame(frame, mode)` | 渡されたBGR画像を認識する |
| `is_open()` / `is_closed()` | 直近の開栓・閉栓フラグを参照する |
| `is_safe()` / `get_status()` | 直近の指定モードの結果・詳細状態を参照する |
| `get_lift_mm()` / `get_detections()` | 浮き量・候補の情報を取得する |
| `get_parameters()` / `set_parameters(...)` | 現在の設定を確認・変更する |
| `save_parameters(path)` / `load_parameters(path)` | JSON設定を保存・復元する |
| `get_image()` / `image_stream()` | JPEG画像・連続画像を取得する |
| `start_camera()` / `stop_camera()` / `release()` | カメラのライフサイクルを管理する |

## ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
