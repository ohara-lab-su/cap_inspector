#!/usr/bin/env python
"""旧ROI設定例に代わる基準線・換算係数の設定例。"""
from cap_inspector import CapInspectorClient

HOST = "10.170.10.55"
PORT = 50051


def main() -> None:
    client = CapInspectorClient(host=HOST, port=PORT)
    try:
        client.set_parameters({"BOTTLE_RIM_Y": 275, "MM_TO_PIXEL": 4.0})
        print(client.get_parameters())
    finally:
        client.close()


if __name__ == "__main__":
    main()
