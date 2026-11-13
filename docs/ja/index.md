# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

OpenCVを利用した赤色キャップの画像認識パッケージです。`grpc_frame` を使用した遠隔運用に対応します。

## 画像認識アルゴリズム：v0.0.0からv0.1.0への変更

**ROIを変更しただけではありません。検出対象の色、候補選択、形状評価、距離の基準、開閉判定の定義を変更しています。**

| 処理段階 | v0.0.0（提供された旧コア） | v0.1.0（`camera9_2.py`ベース） |
|---|---|---|
| 探索領域 | 画像の中央上部を比率で指定するROI（初期値：横30–70%、縦0–35%） | フレーム全体。ROIによる切り出しは行わない |
| 色の抽出 | HSVで低彩度・高輝度の**白色**を抽出（初期値：H 0–180、S 0–30、V 170–255） | HSVの2区間で**赤色**を抽出（H 0–10 / 170–180、S 120–255、V 70–255）し、マスクを結合 |
| マスク整形 | 3×3カーネル、クロージング→オープニング | 5×5カーネル、オープニング→クロージング |
| 輪郭候補 | 面積800以上、ROI中央付近、ROI全体を占める領域を除外。候補のうち最大面積を選択 | 面積500**超**の外部輪郭をすべて処理。最大輪郭への一本化はしない |
| 位置・形状 | `boundingRect`で幅・高さ・底面を取得し、`minAreaRect`で角度を算出 | `minAreaRect`の回転矩形から角度・縦横比・底辺2頂点を算出 |
| 傾き判定 | 校正時の角度との差を許容角度と比較 | 水平からの角度が3°未満、かつ幅/高さが2.3–2.8 |
| 距離の基準 | 正常閉栓キャップを`calibrate()`で撮影し、その底面位置を基準とする | 画像上で設定した瓶の基準線 `BOTTLE_RIM_Y`（初期値275 px）を基準とする |
| mm換算 | 校正キャップの実幅（初期値30 mm）÷撮影幅からmm/pxを求める | 固定換算係数 `MM_TO_PIXEL`（初期値4 px/mm）で割る |
| 閉栓判定 | 校正時の底面からのずれ（初期値±1 mm）に加え、角度差とキャップの幅・高さの差（初期値各25%以内）を評価 | 基準線からの底面浮き量が0.5±1.0 mm、かつ傾き・縦横比条件を満たす |
| 開栓判定 | 校正底面から上方への移動量が初期値**5 mm以上**、かつ角度差が許容内 | 基準線からの底面浮き量が3.5±1.0 mm、かつ傾き・縦横比条件を満たす |
| 判定の状態管理 | `is_open()` / `is_closed()` も撮影・再判定を行い、内部モードを一時変更 | `inspect(mode)` が撮影・両条件の評価・状態更新を行い、`is_open()` / `is_closed()` は直近のフラグのみ返す |

v0.1.0の浮き量は `lift_mm = (BOTTLE_RIM_Y - cap_bottom_y) / MM_TO_PIXEL` です。`cap_bottom_y` は回転矩形のY座標が大きい2頂点の平均です。開栓・閉栓はそれぞれ目標値からの**絶対偏差**で判定するため、v0.0.0の「開栓は最低5 mm以上」という片側閾値とは意味が異なります。

**移行上の注意：** v0.1.0では白色キャップの認識や校正結果を引き継ぎません。`BOTTLE_RIM_Y`、`MM_TO_PIXEL`、目標浮き量、許容差は撮影系に合わせて設定する必要があります。また、v0.0.0の閉栓判定にあった校正キャップとの幅・高さの一致条件は、v0.1.0では回転矩形の縦横比条件に置き換わっており、同等のチェックではありません。複数の有効輪郭がある場合、v0.1.0は全輪郭を評価しますが、状態取得の代表値は最後に処理した輪郭に対応します。


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
