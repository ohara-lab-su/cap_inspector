# APIと設定

`CapInspector.inspect(mode)` は1フレームを撮影・認識し、指定された `"closed"` または `"opened"` の条件を満たすか返します。同じ検査で開栓・閉栓の両フラグを更新します。`is_open()`、`is_closed()`、`is_safe()`、`get_status()` は直近の状態を参照し、再認識しません。

`get_image()` と `image_stream()` は画像取得・配信を担当します。gRPCメソッドの公開には `grpc_frame` を使用します。

設定の取得・変更には `get_parameters()` と `set_parameters()`、または個別setterの `set_camera_id()`、`set_bottle_rim_y()`、`set_mm_to_PIXEL()`、`set_target_close_mm()`、`set_target_open_mm()`、`set_tolerance_mm()`、`set_mode()` を使用します。JSON形式の設定保存・読込には `save_parameters()` と `load_parameters()` を使用します。

gRPCクライアントの型スタブ（`client.pyi`）はパッケージ開発・配布担当者が `server_grpc/make_pyi.py` を使用して生成し、配布物に同梱します。利用者が生成する必要はありません。
