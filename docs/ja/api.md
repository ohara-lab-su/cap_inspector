# APIと設定

`CapInspector.inspect(mode)` がフレーム取得と画像認識を実行し、直近の状態を更新して指定モードの真偽値を返します。`is_open()`、`is_closed()`、`is_safe()`、`get_status()` は保持済みの状態を参照し、再認識しません。

`get_image()` と `image_stream()` は画像を提供します。gRPC公開は `grpc_frame` が担当し、個別のgRPCサービス実装は不要です。

設定取得は `get_parameters()`、一括変更は `set_parameters()`、個別変更は `set_camera_id`、`set_bottle_rim_y`、`set_mm_to_PIXEL`、`set_target_close_mm`、`set_target_open_mm`、`set_tolerance_mm`、`set_mode` を使用します。コンストラクタ引数は初期値です。JSON保存・読込には `save_parameters()` と `load_parameters()` を使用します。

パッケージの開発・配布担当者がリリースのビルド前に開発環境で `python -m cap_inspector.server_grpc.make_pyi` を実行します。既存の `grpc_frame.make_pyi` を呼び出して `src/cap_inspector/server_grpc/client.pyi` を生成し、配布パッケージに含めます。利用者がスタブを生成する必要はありません。
