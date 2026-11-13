# cap_inspector

[![English](https://img.shields.io/badge/lang-en-blue)](https://ohara-lab-su.github.io/cap_inspector/en/index.html) [![日本語](https://img.shields.io/badge/lang-ja-blue)](https://ohara-lab-su.github.io/cap_inspector/ja/index.html) [![GitHub](https://img.shields.io/badge/GitHub-repository-black)](https://github.com/ohara-lab-su/cap_inspector) [![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue)](https://ohara-lab-su.github.io/cap_inspector/) [![Ohara Lab](https://img.shields.io/badge/Ohara-Lab-green)](https://ohara-lab-su.github.io/)

キャップの開閉を、カメラ画像から抽出した輪郭の形状・傾き・底面位置と、明示的な浮き量の許容範囲に基づいて判定するPythonパッケージです。認識の安定性と再現性を高め、照明条件による検出失敗を抑えることを目的としています。赤色・黒色のキャップを扱う構想ですが、現在の色抽出コードは赤色用です。

## ドキュメントの構成

- **利用ガイド**：設置条件、検査アルゴリズム、判定基準、設定方法。
- **APIの使い方**：`inspect()` と状態取得、画像取得、パラメータ管理、gRPCの責務と利用方法。
- **使用例**：ローカル・遠隔検査、GUI、設定ファイルの利用。
- **自動生成API**：ソースコードのGoogle-style docstringから生成するクラス・メソッドリファレンス。

```{toctree}
:maxdepth: 2
:caption: 目次

guide
api_guide
examples
api/modules
```
