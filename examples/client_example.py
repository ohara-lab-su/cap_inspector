#!/usr/bin/env python
"""gRPC経由のキャップ開閉判定例。"""
from cap_inspector import CapInspectorClient

HOST = "10.170.10.55"
PORT = 50051

if __name__ == "__main__":
    camera = CapInspectorClient(HOST, PORT)
    try:
        camera.start_camera()
        print("parameters:", camera.get_parameters())
        # 基準線とmm換算係数は事前に設定した値を使用する。
        # 必要ならset_parameters()またはload_parameters()で変更する。
        camera.set_parameters({"mode": "opened"})
        print("OPEN:", camera.inspect(), camera.get_status())
        camera.set_parameters({"mode": "closed"})
        print("CLOSE:", camera.inspect(), camera.get_status())
    finally:
        camera.stop_camera()
        camera.close()
