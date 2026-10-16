from cap_inspector import CapInspectorClient


HOST = "10.170.10.55"
PORT = 50051


if __name__ == "__main__":
    # cap_inspectorモジュール側で実装されたクライアントを使用する。
    camera = CapInspectorClient(HOST, PORT)

    camera.start_camera()

    camera.set_parameters(
        {
            "roi_x_range": (0.30, 0.70),
            "roi_y_range": (0.00, 0.35),
            "angle_limit": 3.0,
            "threshold_val": 170,
            "cap_actual_width_mm": 30.0,
            "position_limit_mm": 1.0,
        }
    )

    print("parameters:", camera.get_parameters())

    # 正常に閉じたCAPを基準としてキャリブレーションする。
    calibrated = camera.calibrate()
    print("calibrate():", calibrated)

    if not calibrated:
        print("status:", camera.get_status())
        camera.stop_camera()
        camera.close()
        raise RuntimeError("CAP calibration failed")

    print("reference_cap:", camera.get_reference_cap())

    ############
    # ロボット OPEN 動作
    ############

    opened = camera.is_open()
    print("is_open():", opened)
    print("status:", camera.get_status())

    if not opened:
        # OPEN後のCAP状態が正常でない場合の停止処理をここに記述する。
        pass

    ############
    # ロボット CLOSE 動作
    ############

    closed = camera.is_closed()
    print("is_closed():", closed)
    print("status:", camera.get_status())

    if not closed:
        # CLOSE後のCAP状態が正常でない場合の停止処理をここに記述する。
        pass

    camera.stop_camera()
    camera.close()
