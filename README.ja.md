# cap_inspector

[English](README.md) | [日本語](README.ja.md) | [ドキュメント](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) | [GitHub](https://github.com/ohara-lab-su/cap_inspector)

OpenCVを用いてボトルキャップの開閉状態を検査する画像認識パッケージです。主眼はキャップの色の変更ではなく、**認識アルゴリズムと判定基準の明確化による検査の安定性・再現性の向上**にあります。照明条件の変動による誤検出・検出失敗を抑えることを目的として、候補領域の抽出後に形状・傾き・底面位置を評価し、浮き量を数値的に判定します。赤色だけでなく黒色のキャップも対象とするプロジェクトです。ローカルカメラでの検査、JSONによる設定管理、gRPCによる遠隔操作・画像配信、GUIビューアーに対応します。

## 画像認識と開閉判定

現行の赤色キャップ向け検出設定では、以下の処理を使用します。色抽出条件は検出対象に依存し、黒色キャップに同じHSV閾値を適用するものではありません。照明変動に対する完全な不変性を保証するものではなく、撮影条件と検出設定の適合が必要です。

1. カメラ画像をHSV色空間に変換し、赤色の2領域（H 0–10、170–180、S 120–255、V 70–255）を抽出してマスクを結合します。
2. 5 × 5カーネルによるオープニング、クロージングの順にマスクを整形します。外部輪郭を抽出し、面積500 pixel²を超える輪郭を処理します。
3. 各輪郭に最小面積回転矩形を当てはめ、傾きが3°未満、幅と高さの比が2.3–2.8であることを確認します。
4. 回転矩形のY座標が大きい2頂点からキャップ底面を求め、瓶の基準線からの浮き量を計算します。

   `lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL`

5. 浮き量を開栓・閉栓それぞれの目標値と比較します。初期値は閉栓0.5 mm、開栓3.5 mm、許容差はそれぞれ±1.0 mmです。

基準線と画素・距離換算係数は撮影系の幾何条件に依存するため、設置環境に合わせて設定します。条件を満たす輪郭をすべて処理し、現在の代表状態には最後に処理した輪郭の結果を保持します。キャップを検出できなかったフレームは検査不合格です。

`inspect(mode)` は1フレームの撮影・画像認識を行い、開栓・閉栓の両フラグを更新して、`"closed"` または `"opened"` の指定条件に対する判定結果を返します。`is_closed()` と `is_open()` は直近のフラグを返すだけで再撮影しません。取得できる状態は直近の検査時点のものであり、連続監視値ではありません。

## インストール

```bash
pip install .
```

開発時は `pip install -e .` を利用できます。依存パッケージの配布名は `grpc-frame` と `xlogger-py` です（Pythonのimport名は `grpc_frame` と `x_logger`）。GUIにはPySide6を使用します。

## 基本的な使い方

```python
from cap_inspector import CapInspector

inspector = CapInspector(current_mode="closed")
try:
    passed = inspector.inspect("closed")
    print(passed, inspector.is_closed(), inspector.is_open())
finally:
    inspector.release()
```

## gRPCとGUI

`python examples/server_example.py` でサーバーを起動し、クライアント側で `python examples/gui_client.py` を実行します。接続先は使用例のスクリプトで設定します。遠隔GUIを運用用ビューアーとし、ローカルビューアーと `run()` はテスト用です。判定やパラメータ設定の例は `examples/` にあります。

## ドキュメント

- [APIリファレンス](https://ohara-lab-su.github.io/cap_inspector/ja/api_guide.html)
- [使用例](https://ohara-lab-su.github.io/cap_inspector/ja/examples.html)
- [自動生成Python API](https://ohara-lab-su.github.io/cap_inspector/ja/api/modules.html)
- [変更履歴](CHANGELOG.ja.md)

## ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE) を参照してください。
