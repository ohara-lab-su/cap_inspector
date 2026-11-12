import json

from grpc_frame.grpc_client import GrpcClient


class CapInspectorClient(GrpcClient):
    """CapInspector 用 gRPC クライアント。

    grpc_frame の動的 API をそのまま利用しつつ、クライアントの用途を
    CapInspector に限定して明確にするためのクラス。
    """

    def __init__(self, host="127.0.0.1", port=50051, grpc_options=None):
        if grpc_options is None:
            grpc_options = (("grpc.max_receive_message_length", 16 * 1024 * 1024),)
        super().__init__(host, port, grpc_options=grpc_options)

        # GrpcClient.__init__() は Describe の結果から同名メソッドを
        # インスタンス属性として動的バインドする。image_stream は通常の
        # Call ではなく StreamCall を使う必要があるため、その動的バインドを
        # 除去して、このクラスで定義した image_stream() を有効にする。
        for method_name in (
            "image_stream",
            "save_parameters",
            "load_parameters",
        ):
            if method_name in self.__dict__:
                del self.__dict__[method_name]

    def save_parameters(self, filename: str):
        """serverの現在値を取得し、client側ファイルへ保存する。"""
        parameters = self.get_parameters()
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(parameters, file, ensure_ascii=False, indent=2)
        return parameters

    def load_parameters(self, filename: str):
        """client側ファイルを読み込み、serverへ認識パラメータを設定する。"""
        with open(filename, "r", encoding="utf-8") as file:
            parameters = json.load(file)
        return self.set_parameters(parameters)

    def image_stream(self, jpeg_quality: int = 85, interval_sec: float = 0.1):
        """画像ストリームを server-streaming RPC で取得する。"""
        return self.stream_call("image_stream", jpeg_quality, interval_sec)
