# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-ja-blue)](README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCVを利用した赤色キャップの位置・傾斜・開閉状態判定用Pythonパッケージです。`grpc_frame` によりサーバー上の画像認識を遠隔操作できます。

[English README](README.md) · [日本語ドキュメント](docs/ja/index.md) · [English docs](docs/en/index.md)

## 主な機能

- HSV赤色領域抽出、輪郭・傾斜・アスペクト比・底面高さの評価。
- `inspect(mode)` は1フレームを取得し、開栓・閉栓条件を同時に評価して、指定モードの結果を `bool` で返します。
- `is_open()`、`is_closed()`、`is_safe()`、`get_status()` は直近の判定結果を参照するだけで、再撮影・再判定しません。
- 個別setter、一括設定、JSON保存・読込、JPEG画像取得、ストリーミング、gRPCクライアントGUI。
- `run()` はローカル検証用です。通常運用のビューアーは `examples/gui_client.py` です。

## インストール

```bash
pip install -e .
```

配布パッケージ名は `grpc-frame`、`xlogger-py` で、Pythonのimport名はそれぞれ `grpc_frame`、`x_logger` です。GUIにはPySide6が必要です。

## 使用例

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

サーバーは `python examples/server_example.py`、gRPCクライアントGUIは `python examples/gui_client.py` で起動します。接続先は各スクリプト内のHOST/PORTを設定してください。個別・一括パラメータ設定は `examples/set_parameters_client.py`、JSON設定は `examples/parameter_client.py` を参照してください。

## 型スタブ生成

パッケージの開発・配布担当者が、リリースのビルド前に開発環境で `python -m cap_inspector.server_grpc.make_pyi` を実行し、`src/cap_inspector/server_grpc/client.pyi` を生成します。この処理は既存の `grpc_frame.make_pyi` を呼び出すもので、独自のスタブ生成処理は実装しません。生成した `client.pyi` は配布パッケージに含めます。利用者によるスタブ生成は不要です。

## 運用上の注意

`get_image()` と `image_stream()` は画像を取得して判定状態を更新します。複数クライアントから同一インスタンスを使用すると、最後に処理したフレームが保持されます。`is_open()` と `is_closed()` 自体は状態を更新しません。開栓・閉栓の許容範囲が重なる設定では、両フラグがTrueになる可能性があります。

## ライセンス

Apache-2.0。`LICENSE` を参照してください。
