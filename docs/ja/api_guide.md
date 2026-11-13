# APIの使い方（手動解説）

このページはAPIの責務と利用方法を説明します。引数・戻り値・メソッドのdocstringは[自動生成Python API](api/modules.html)を参照してください。

## 検査と状態取得

`CapInspector.inspect(current_mode=None)` はカメラから画像を取得して指定モードで判定します。`process_frame(frame, current_mode=None)` は既存のBGR画像を判定します。いずれも直近の判定状態を更新します。`is_open()` と `is_closed()` はフラグの参照のみです。`is_safe()` は指定モードの直近の結果、`get_status()` は `is_safe`、`reason`、`is_open`、`is_closed` を含む辞書を返します。

## 検出結果と位置情報

`get_detection()` は代表輪郭、`get_detections()` は検出した輪郭の一覧を返します。`get_lift_mm()`、`get_bottom_points()`、`get_box_shape()` は直近の位置情報を返します。基準線と画素換算係数は対応するgetter/setterで確認・変更できます。

## カメラと画像配信

`start_camera()`、`stop_camera()` でカメラを制御し、`release()` で解放します。`get_image()` はJPEG画像を、`image_stream()` は連続画像を提供します。

## gRPCによる遠隔操作

`cap_inspector.server_grpc.CapInspectorClient` は `grpc_frame.grpc_client.GrpcClient` を継承します。サーバーは `grpc_frame` を通じてメソッドを公開し、`image_stream()` はストリーミングRPCを使用します。クライアント側の `save_parameters()` / `load_parameters()` はローカルJSONを読み書きしてサーバー設定と同期します。gRPCクライアントの型スタブは開発・配布側が生成して同梱するもので、利用者は生成しません。
