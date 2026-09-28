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
