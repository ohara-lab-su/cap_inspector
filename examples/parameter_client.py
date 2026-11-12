from cap_inspector import CapInspectorClient


HOST = "10.170.10.55"
PORT = 50051
PARAMETER_FILE = "cap_inspector_parameters.json"


def main():
    client = CapInspectorClient(host=HOST, port=PORT)

    # CLIから直接変更する場合。
    client.set_parameters(
        {
            "angle_limit": 3.0,
            "threshold_val": 170,
            "min_aspect_ratio": 1.5,
            "smooth_frames": 3,
            "cap_actual_width_mm": 30.0,
            "position_limit_mm": 1.0,
        }
    )

    # serverの現在値をclient側マシンへ保存する。
    client.save_parameters(PARAMETER_FILE)

    # client側ファイルを読み、serverへset_parameters()する。
    client.load_parameters(PARAMETER_FILE)

    print(client.get_parameters())
    client.close()


if __name__ == "__main__":
    main()
