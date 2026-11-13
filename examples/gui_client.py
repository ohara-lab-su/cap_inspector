#!/usr/bin/env python
"""gRPC 接続による CapInspector 本番用ビューアー。"""

from cap_inspector.server_grpc import CapInspectorClient
from cap_inspector.viewer import run_viewer


HOST = "127.0.0.1"
PORT = 50051
JPEG_QUALITY = 85
INTERVAL_SEC = 0.1


def main() -> None:
    client = CapInspectorClient(HOST, PORT)
    try:
        run_viewer(
            inspector=client,
            close_callback=client.close,
            jpeg_quality=JPEG_QUALITY,
            interval_sec=INTERVAL_SEC,
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
