from cap_inspector.server_grpc import CapInspectorClient
from cap_inspector.viewer import run_viewer


# HOST = "10.170.10.55"
HOST = "127.0.0.1"
PORT = 50051

# このファイルはGUIクライアントを実行しているPC上で読み書きする。
# server側へファイル名を送らない。
PARAMETER_FILE = "cap_inspector_parameters.json"

JPEG_QUALITY = 85
INTERVAL_SEC = 0.1


if __name__ == "__main__":
    client = CapInspectorClient(HOST, PORT)
    run_viewer(
        inspector=client,
        close_callback=client.close,
        jpeg_quality=JPEG_QUALITY,
        interval_sec=INTERVAL_SEC,
        parameter_file=PARAMETER_FILE,
    )
