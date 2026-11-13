#!/usr/bin/env python
"""gRPC 経由で稼働中の CapInspector の認識パラメータを変更・確認する例。"""

from cap_inspector import CapInspectorClient

HOST = "10.170.10.55"
PORT = 50051

# 指定しないパラメータは変更しない。
PARAMETERS = {
    "camera_id": 0,
    "BOTTLE_RIM_Y": 275,
    "MM_TO_PIXEL": 4.0,
    "TARGET_CLOSE_MM": 0.5,
    "TARGET_OPEN_MM": 3.5,
    "TOLERANCE_MM": 1.0,
    "mode": "closed",
}


def main() -> None:
    client = CapInspectorClient(host=HOST, port=PORT)
    try:
        print("変更前:", client.get_parameters())

        # 個別の setter による設定（必要な行だけ実行する）。
        client.set_camera_id(0)
        client.set_bottle_rim_y(275)
        client.set_mm_to_PIXEL(4.0)
        client.set_target_close_mm(0.5)
        client.set_target_open_mm(3.5)
        client.set_tolerance_mm(1.0)
        client.set_mode("closed")
        print("個別設定後:", client.get_parameters())

        # 複数パラメータを一括で設定する場合。
        client.set_parameters(PARAMETERS)
        after = client.get_parameters()
        print("一括設定後:", after)
        for key, value in PARAMETERS.items():
            if after[key] != value:
                raise AssertionError(f"設定値が反映されていません: {key}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
