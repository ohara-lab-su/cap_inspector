# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCVを利用した赤色キャップの画像認識パッケージです。`grpc_frame` を使用した遠隔運用に対応します。

## 動作

`inspect(mode)` は画像を1フレーム取得し、開栓・閉栓の両条件を評価したうえで、指定モード（`opened` または `closed`）の判定を真偽値で返します。`is_open()`、`is_closed()`、`get_status()` は直近の結果を読み出し、撮影しません。

通常運用は `examples/gui_client.py` の遠隔ビューアーを使用します。`run()` とローカルビューアーはテスト用です。

## パラメータ

コンストラクタ引数は初期値です。運用中の変更には個別の `set_xxx()` または `set_parameters()` を使用します。旧ROI方式の代わりに `BOTTLE_RIM_Y` と `MM_TO_PIXEL` を設定します。個別・一括設定例は `examples/set_parameters_client.py` を参照してください。

## 使用例

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## ドキュメント

- [APIと使用方法](api.md)
- [使用例](examples.md)
- [English](../en/index.html)
