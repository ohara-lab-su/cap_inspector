#!/usr/bin/env python
"""クライアント側JSONでサーバーの認識パラメータを設定する。"""
from cap_inspector import CapInspectorClient

HOST = "10.170.10.55"
PORT = 50051
PARAMETER_FILE = "cap_inspector_parameters.json"


def main() -> None:
    client = CapInspectorClient(host=HOST, port=PORT)
    try:
        client.load_parameters(PARAMETER_FILE)
        print(client.get_parameters())
        client.save_parameters(PARAMETER_FILE)
    finally:
        client.close()


if __name__ == "__main__":
    main()
