# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-ja-blue)](README.ja.md) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCVを用いて瓶の赤色キャップを検出し、キャップの位置と傾きから開栓・閉栓状態を判定するPythonパッケージです。ローカルカメラでの検査に加え、`grpc_frame` を利用した遠隔操作と画像配信に対応します。

[English README](README.md) | [日本語ドキュメント](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) | [変更履歴](CHANGELOG.ja.md)

## 主な機能

- HSV色空間の2つの赤色領域を利用したキャップ検出。
- 輪郭の回転矩形による傾斜・縦横比・底面位置の評価。
- 瓶の基準線からのキャップ浮き量に基づく開栓・閉栓判定。
- `inspect(mode)` による検査実行と、`is_open()`・`is_closed()` による直近の結果の取得。
- パラメータの変更、JSON形式での保存・読込。
- gRPCによる遠隔検査、画像取得・ストリーミング、GUIビューアー。

## インストール

プロジェクトのルートディレクトリで実行します。

```bash
pip install .
```

開発時は `pip install -e .` も使用できます。依存パッケージの配布名は `grpc-frame`、`xlogger-py` です（Pythonでのimport名は `grpc_frame`、`x_logger`）。GUIにはPySide6を使用します。

## 基本的な使い方

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    result = inspector.inspect("closed")
    print(result)
    print(inspector.is_closed())
    print(inspector.is_open())
finally:
    inspector.release()
```

`inspect("closed")` は閉栓条件、`inspect("opened")` は開栓条件を検査します。どちらの場合も同じフレームから両方の状態を評価します。`is_open()` と `is_closed()` は最後の検査結果を返すだけで、新たな撮影や画像認識は行いません。

## gRPCサーバーとGUI

サーバーを起動します。

```bash
python examples/server_example.py
```

別の端末からGUIクライアントを起動します。

```bash
python examples/gui_client.py
```

接続先のホストとポートは、各サンプルスクリプトの設定に合わせてください。パラメータ設定やクライアント操作の例は `examples/` を参照してください。

## 判定方式

v0.1.0では赤色キャップを画像全体から抽出し、回転矩形の底面と瓶の基準線との距離を用いて判定します。開栓・閉栓の目標浮き量と許容差は個別に設定できます。撮影位置や倍率に応じて `BOTTLE_RIM_Y` と `MM_TO_PIXEL` を設定してください。

旧版v0.0.0は白色キャップをROI内で検出し、校正済みの閉栓キャップとの相対差を判定する方式でした。**両バージョンでは検出対象と判定アルゴリズムが異なります。** 詳細な比較は[技術ドキュメント](https://ohara-lab-su.github.io/cap_inspector/ja/index.html)を、バージョンごとの変更は[CHANGELOG](CHANGELOG.ja.md)を参照してください。

## ドキュメント

- [日本語ドキュメント](https://ohara-lab-su.github.io/cap_inspector/ja/index.html)
- [APIリファレンス](https://ohara-lab-su.github.io/cap_inspector/ja/api.html)
- [使用例](https://ohara-lab-su.github.io/cap_inspector/ja/examples.html)
- [変更履歴](CHANGELOG.ja.md)

型スタブ `client.pyi` はパッケージの開発・配布担当者が生成して配布物に含めるものです。利用者が生成する必要はありません。

## ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
