from collections import deque
import time

import cv2
import numpy as np
from x_logger import XLogger


class CapInspector:

    def __init__(
        self,
        camera_id=1,
        roi_x_range=(0.30, 0.70),  # ROI横幅 (30%〜70%)
        roi_y_range=(0.0, 0.35),  # ROI高さ (0%〜35%)
        #
        angle_limit=3.0,  # 許容角度（度）
        threshold_val=170,
        min_aspect_ratio=1.5,
        smooth_frames=3,
        mode="closed",  # デフォルトの判定モード ("closed" または "open")
        cap_actual_width_mm=30.0,  # 実際のキャップ横幅(mm)
        position_limit_mm=1.0,  # 閉栓時に許容する基準位置からのずれ(mm)
        logger=None,
    ):
        """カメラと検出パラメータの初期化"""
        self.camera_id = camera_id
        self.roi_x_range = roi_x_range
        self.roi_y_range = roi_y_range
        self.angle_limit = angle_limit
        self.min_aspect_ratio = min_aspect_ratio
        self.cap = None
        self.angle_history = deque(maxlen=smooth_frames)
        self.smooth_frames = smooth_frames
        self.threshold_val = threshold_val
        self.mode = mode
        self.cap_actual_width_mm = cap_actual_width_mm
        self.position_limit_mm = position_limit_mm
        self._is_safe = None
        self._reason = None

        # 正常に閉じたCAPを基準として保存する。
        self.reference_cap = None

        if logger is not None:
            self.logger = logger
        else:
            self.logger = XLogger(logger_name="cap_inspector")

        self.logger.info(
            f"CapInspector initialized: camera_id={self.camera_id}, "
            f"roi_x_range={self.roi_x_range}, roi_y_range={self.roi_y_range}, "
            f"angle_limit={self.angle_limit}, threshold_val={self.threshold_val}, "
            f"min_aspect_ratio={self.min_aspect_ratio}, smooth_frames={self.smooth_frames}"
        )

    def __del__(self):
        """デストラクタでリソースを解放する。"""
        try:
            self.release()
        except Exception:
            pass

    def start_camera(self):
        """カメラの開始"""
        self.logger.info(f"Camera open requested: camera_id={self.camera_id}")
        self.cap = cv2.VideoCapture(self.camera_id)
        opened = self.cap.isOpened()
        if opened:
            self.logger.info(f"Camera opened: camera_id={self.camera_id}")
        else:
            self.logger.error(f"Camera open failed: camera_id={self.camera_id}")
        return opened

    def _detect_cap(self, frame, draw_roi=True):
        """ROI内からCAPを検出し、画像上の位置・大きさ・角度を返す。"""
        height, width, _ = frame.shape

        # 1. ROI（注目領域）の設定
        roi_start_x = int(width * self.roi_x_range[0])
        roi_end_x = int(width * self.roi_x_range[1])
        roi_start_y = int(height * self.roi_y_range[0])
        roi_end_y = int(height * self.roi_y_range[1])

        if roi_start_x < 0:
            roi_start_x = 0
        if roi_start_y < 0:
            roi_start_y = 0
        if roi_end_x > width:
            roi_end_x = width
        if roi_end_y > height:
            roi_end_y = height

        if roi_end_x <= roi_start_x or roi_end_y <= roi_start_y:
            return None, "FAIL: Invalid ROI"

        print(f"ROI設定完了: x={roi_start_x}-{roi_end_x}, y={roi_start_y}-{roi_end_y}")

        roi = frame[roi_start_y:roi_end_y, roi_start_x:roi_end_x]
        roi_h, roi_w, _ = roi.shape
        roi_center_x = roi_w / 2.0

        # ROI視覚化 (青枠)
        if draw_roi:
            cv2.rectangle(
                frame,
                (roi_start_x, roi_start_y),
                (roi_end_x, roi_end_y),
                (255, 0, 0),
                1,
            )

        # 2. HSVによる白の抽出（Sの許容を広げ、V閾値を下げて側面の影もカバー）
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower_white = np.array([0, 0, self.threshold_val])
        upper_white = np.array([180, 30, 255])
        thresh = cv2.inRange(hsv_roi, lower_white, upper_white)

        # クロージング処理（膨張→収縮）で途切れ・隙間を結合する
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # 3. 輪郭検出とターゲット抽出
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        valid_caps = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 800:
                continue

            rx, ry, rw, rh = cv2.boundingRect(cnt)
            print(f"輪郭検出完了: rx={rx}, ry={ry}, rw={rw}, rh={rh}")
            if rh == 0:
                continue

            # aspect_ratio = float(rw) / float(rh)

            # # アスペクト比条件 ＆ ROI中央付近のチェック
            # if self.min_aspect_ratio <= aspect_ratio <= 4.0:
            #     cnt_center_x = rx + (rw / 2.0)
            #     dist_from_center = abs(cnt_center_x - roi_center_x)
            #     print(
            #         f"ROI中央付近のチェック完了: "
            #         f"cnt_center_x={cnt_center_x}, "
            #         f"dist_from_center={dist_from_center}"
            #     )
            #     if dist_from_center < (roi_w * 0.20):
            #         valid_caps.append((area, cnt, rx, ry, rw, rh))

            aspect_ratio = float(rw) / float(rh)

            # CAPが傾くとboundingRectの高さが増えてaspect_ratioが小さくなる。
            # 傾きは後段のminAreaRect()で判定するため、
            # CAP候補の抽出段階ではaspect_ratioによって除外しない。
            cnt_center_x = rx + (rw / 2.0)
            dist_from_center = abs(cnt_center_x - roi_center_x)

            print(
                f"ROI中央付近のチェック完了: "
                f"cnt_center_x={cnt_center_x}, "
                f"dist_from_center={dist_from_center}, "
                f"aspect_ratio={aspect_ratio}"
            )

            if dist_from_center < (roi_w * 0.20):
                valid_caps.append((area, cnt, rx, ry, rw, rh))

        if not valid_caps:
            return None, "FAIL: Cap Not Found"

        # 4. 最も大きな白オブジェクト（本物のキャップ）を選択
        valid_caps.sort(key=lambda item: item[0], reverse=True)
        _, best_cnt, rx, ry, rw, rh = valid_caps[0]

        abs_x = roi_start_x + rx
        abs_top_y = roi_start_y + ry
        abs_bottom_y = abs_top_y + rh

        # === 角度の計算 ===
        rect = cv2.minAreaRect(best_cnt)
        (_, _), (w_r, h_r), rect_angle = rect
        print(f"角度計算完了: rect_angle={rect_angle}, w_r={w_r}, h_r={h_r}")

        if w_r > 0 and h_r > 0:
            if w_r < h_r:
                calc_angle = abs(rect_angle)
            else:
                calc_angle = abs(rect_angle - 90)

            if calc_angle > 45:
                calc_angle = abs(90 - calc_angle)
        else:
            calc_angle = 0.0

        cap_info = {
            "x": abs_x,
            "top_y": abs_top_y,
            "bottom_y": abs_bottom_y,
            "width": rw,
            "height": rh,
            "angle": calc_angle,
        }
        return cap_info, None

    def calibrate(self, frame=None):
        """正常に閉じたCAPを検出し、以後の判定基準として保存する。"""
        if frame is None:
            frame = self._read_frame()

        work_frame = frame.copy()
        cap_info, error = self._detect_cap(work_frame)
        if cap_info is None:
            self._reason = error
            self.logger.warning(f"Calibration failed: {error}")
            return False

        # 基準CAP幅からmm/pixelを固定する。
        cap_info["mm_per_pixel"] = self.cap_actual_width_mm / float(cap_info["width"])
        self.reference_cap = cap_info
        self.angle_history.clear()
        self._is_safe = True
        self._reason = None

        self.logger.info(f"Calibration completed: {self.reference_cap}")
        print(
            "キャリブレーション完了: "
            f"top={cap_info['top_y']}, "
            f"bottom={cap_info['bottom_y']}, "
            f"angle={cap_info['angle']:.2f}deg, "
            f"mm_per_pixel={cap_info['mm_per_pixel']:.4f}"
        )
        return True

    def process_frame(self, frame):
        """1フレームあたりのCAP検出と、キャリブレーション基準による判定"""
        cap_info, error = self._detect_cap(frame)

        if cap_info is None:
            self._draw_stop_message(frame, error)
            print("キャップ検出失敗")
            return frame, False, error

        abs_x = cap_info["x"]
        abs_y = cap_info["top_y"]
        abs_bottom_y = cap_info["bottom_y"]
        rw = cap_info["width"]

        # 角度を平滑化する。
        self.angle_history.append(cap_info["angle"])
        smoothed_angle = sum(self.angle_history) / len(self.angle_history)
        print(f"角度平滑化完了: smoothed_angle={smoothed_angle}")

        is_success = False
        reason = None
        detail_str = f"Angle:{smoothed_angle:.1f}deg"

        if self.reference_cap is None:
            reason = "FAIL: Calibration Required"

        elif self.mode == "open":
            # 開栓後はCAPが傾いていないことを確認する。
            angle_diff = abs(smoothed_angle - self.reference_cap["angle"])
            detail_str = f"AngleDiff:{angle_diff:.1f}deg"

            if angle_diff > self.angle_limit:
                reason = (
                    f"OPEN FAIL: Angle difference "
                    f"{angle_diff:.1f}deg > {self.angle_limit}deg"
                )
            else:
                is_success = True

        elif self.mode == "closed":
            # 閉栓後はキャリブレーション時のCAP上端・下端位置と比較する。
            mm_per_pixel = self.reference_cap["mm_per_pixel"]
            top_diff_mm = (
                abs(cap_info["top_y"] - self.reference_cap["top_y"]) * mm_per_pixel
            )
            bottom_diff_mm = (
                abs(cap_info["bottom_y"] - self.reference_cap["bottom_y"])
                * mm_per_pixel
            )
            angle_diff = abs(smoothed_angle - self.reference_cap["angle"])

            detail_str = (
                f"Top:{top_diff_mm:.2f}mm "
                f"Bottom:{bottom_diff_mm:.2f}mm "
                f"AngleDiff:{angle_diff:.1f}deg"
            )

            if angle_diff > self.angle_limit:
                reason = (
                    f"CLOSED FAIL: Angle difference "
                    f"{angle_diff:.1f}deg > {self.angle_limit}deg"
                )
            elif top_diff_mm > self.position_limit_mm:
                reason = (
                    f"CLOSED FAIL: Top position "
                    f"{top_diff_mm:.2f}mm > {self.position_limit_mm:.2f}mm"
                )
            elif bottom_diff_mm > self.position_limit_mm:
                reason = (
                    f"CLOSED FAIL: Bottom position "
                    f"{bottom_diff_mm:.2f}mm > {self.position_limit_mm:.2f}mm"
                )
            else:
                is_success = True

        else:
            reason = f"FAIL: Unknown mode: {self.mode}"

        # === 結果の描画 ===
        if is_success:
            color = (0, 255, 0)
            status_str = "PASS"
        else:
            color = (0, 0, 255)
            status_str = "FAIL"

        if not is_success:
            self._draw_stop_message(frame, reason)

        cv2.putText(
            frame,
            f"Mode:{self.mode} [{status_str}] {detail_str}",
            (abs_x, max(20, abs_y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

        # 緑枠（判定成功時）/ 赤枠（失敗時）
        cv2.rectangle(
            frame,
            (abs_x, abs_y),
            (abs_x + rw, abs_bottom_y),
            color,
            2,
        )

        # CAP底面の黄色線
        cv2.line(
            frame,
            (abs_x, abs_bottom_y),
            (abs_x + rw, abs_bottom_y),
            (0, 255, 255),
            2,
        )

        # キャリブレーション時のCAP上端・下端を表示する。
        if self.reference_cap is not None:
            ref_top_y = int(self.reference_cap["top_y"])
            ref_bottom_y = int(self.reference_cap["bottom_y"])
            cv2.line(
                frame,
                (abs_x, ref_top_y),
                (abs_x + rw, ref_top_y),
                (255, 255, 0),
                1,
            )
            cv2.line(
                frame,
                (abs_x, ref_bottom_y),
                (abs_x + rw, ref_bottom_y),
                (255, 255, 0),
                1,
            )

        return frame, is_success, reason

    def get_parameters(self):
        """現在の認識パラメータを返す。"""
        return {
            "camera_id": self.camera_id,
            "roi_x_range": self.roi_x_range,
            "roi_y_range": self.roi_y_range,
            "angle_limit": self.angle_limit,
            "threshold_val": self.threshold_val,
            "min_aspect_ratio": self.min_aspect_ratio,
            "smooth_frames": self.smooth_frames,
            "mode": self.mode,
            "cap_actual_width_mm": self.cap_actual_width_mm,
            "position_limit_mm": self.position_limit_mm,
        }

    def set_parameters(self, parameters):
        """認識パラメータをまとめて更新する。既存キーのみ受け付ける。"""
        self.logger.info(f"Parameter update requested: {parameters}")
        allowed = {
            "camera_id",
            "roi_x_range",
            "roi_y_range",
            "angle_limit",
            "threshold_val",
            "min_aspect_ratio",
            "smooth_frames",
            "mode",
            "cap_actual_width_mm",
            "position_limit_mm",
        }
        unknown = set(parameters) - allowed
        if unknown:
            self.logger.warning(f"Unknown parameters rejected: {sorted(unknown)}")
            raise ValueError(f"unknown parameters: {sorted(unknown)}")

        if "camera_id" in parameters:
            self.camera_id = int(parameters["camera_id"])
        if "roi_x_range" in parameters:
            self.roi_x_range = tuple(float(v) for v in parameters["roi_x_range"])
        if "roi_y_range" in parameters:
            self.roi_y_range = tuple(float(v) for v in parameters["roi_y_range"])
        if "angle_limit" in parameters:
            self.angle_limit = float(parameters["angle_limit"])
        if "threshold_val" in parameters:
            self.threshold_val = int(parameters["threshold_val"])
        if "min_aspect_ratio" in parameters:
            self.min_aspect_ratio = float(parameters["min_aspect_ratio"])
        if "smooth_frames" in parameters:
            self.smooth_frames = int(parameters["smooth_frames"])
            self.angle_history = deque(
                self.angle_history,
                maxlen=self.smooth_frames,
            )
        if "mode" in parameters:
            self.mode = str(parameters["mode"])
        if "cap_actual_width_mm" in parameters:
            self.cap_actual_width_mm = float(parameters["cap_actual_width_mm"])
        if "position_limit_mm" in parameters:
            self.position_limit_mm = float(parameters["position_limit_mm"])

        current = self.get_parameters()
        self.logger.info(f"Parameters updated: {current}")
        return current

    def inspect(self):
        """現在の1フレームを判定し、判定状態を更新する。"""
        frame = self._read_frame()
        _, is_safe, reason = self.process_frame(frame)
        self._is_safe = bool(is_safe)
        self._reason = reason
        self.logger.debug(
            f"Inspection completed: is_safe={self._is_safe}, reason={self._reason}"
        )
        return self._is_safe

    def is_safe(self):
        """直近の inspect() による判定結果を返す。未判定時は None。"""
        return self._is_safe

    def get_status(self):
        """直近の inspect() による判定状態を返す。認識処理は実行しない。"""
        return {"is_safe": self._is_safe, "reason": self._reason}

    def get_image(self, jpeg_quality=85):
        """現在の認識結果を描画したJPEG画像を bytes で返す。"""
        frame = self._read_frame()
        processed_frame, is_safe, reason = self.process_frame(frame)
        ok, encoded = cv2.imencode(
            ".jpg",
            processed_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)],
        )
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        return {
            "image": encoded.tobytes(),
            "is_safe": bool(is_safe),
            "reason": reason,
        }

    def image_stream(self, jpeg_quality=85, interval_sec=0.1):
        """GUI確認用に認識結果JPEGを連続配信する generator。"""
        self.logger.info(
            f"Image stream started: jpeg_quality={jpeg_quality}, "
            f"interval_sec={interval_sec}"
        )
        try:
            while True:
                yield self.get_image(jpeg_quality=jpeg_quality)
                if interval_sec > 0:
                    time.sleep(float(interval_sec))
        except GeneratorExit:
            self.logger.info("Image stream closed by client")
            raise
        except Exception:
            self.logger.exception("Image stream failed")
            raise
        finally:
            self.logger.info("Image stream stopped")

    def _read_frame(self):
        """カメラから1フレーム取得する。未起動なら自動的に開始する。"""
        if self.cap is None or not self.cap.isOpened():
            if not self.start_camera():
                raise RuntimeError(f"camera open failed: camera_id={self.camera_id}")
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("camera frame read failed")
        return frame

    def _draw_stop_message(self, frame, message):
        """停止警告テキストの描画"""
        cv2.putText(
            frame,
            message,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
        )

    def run(self):
        """メインループ"""
        if not self.start_camera():
            print("カメラの起動に失敗しました。")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("カメラの読み込みに失敗しました。")
                break

            processed_frame, is_safe, reason = self.process_frame(frame)
            cv2.imshow("Webcam - White Cap Detection", processed_frame)

            if not is_safe:
                print(f"【停止通知】{reason}")
                cv2.waitKey(2000)
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("【停止通知】STOP キーが押されました。")
                break

        self.release()

    def stop_camera(self):
        """カメラを停止して解放する。"""
        self.logger.info("Camera stop requested")
        if self.cap:
            self.cap.release()
            self.cap = None
            self.logger.info("Camera released")

    def release(self):
        """リソースの解放"""
        self.logger.info("CapInspector release requested")
        self.stop_camera()
        cv2.destroyAllWindows()
        self.logger.info("CapInspector released")


# --- 実行用コード ---
if __name__ == "__main__":
    camera_id = 0
    mode = "closed"
    angle_limit = 3.0
    cap_actual_width_mm = 30.0
    position_limit_mm = 1.0
    min_aspect_ratio = 1.5
    threshold_val = 170
    roi_x_range = (0.40, 0.60)
    roi_y_range = (0.0, 0.35)

    logger = XLogger()
    detector = CapInspector(
        camera_id=camera_id,
        mode=mode,
        angle_limit=angle_limit,
        cap_actual_width_mm=cap_actual_width_mm,
        position_limit_mm=position_limit_mm,
        min_aspect_ratio=min_aspect_ratio,
        threshold_val=threshold_val,
        roi_x_range=roi_x_range,
        roi_y_range=roi_y_range,
        logger=logger,
    )

    window_name = "Cap Inspector - ROI / Calibration Test"

    # ROIをマウスで指定するための状態
    mouse_state = {
        "dragging": False,
        "start_x": 0,
        "start_y": 0,
        "end_x": 0,
        "end_y": 0,
        "frame_width": 0,
        "frame_height": 0,
    }

    def mouse_callback(event, x, y, flags, param):
        """ライブ画像上のドラッグ操作からROIを設定する。"""
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_state["dragging"] = True
            mouse_state["start_x"] = x
            mouse_state["start_y"] = y
            mouse_state["end_x"] = x
            mouse_state["end_y"] = y
            print(f"ROI選択開始: ({x}, {y})")

        elif event == cv2.EVENT_MOUSEMOVE:
            if mouse_state["dragging"]:
                mouse_state["end_x"] = x
                mouse_state["end_y"] = y

        elif event == cv2.EVENT_LBUTTONUP:
            if not mouse_state["dragging"]:
                return

            mouse_state["dragging"] = False
            mouse_state["end_x"] = x
            mouse_state["end_y"] = y

            frame_width = mouse_state["frame_width"]
            frame_height = mouse_state["frame_height"]

            if frame_width <= 0 or frame_height <= 0:
                print("フレームサイズが未確定のためROIを変更できません。")
                return

            start_x = min(mouse_state["start_x"], mouse_state["end_x"])
            end_x = max(mouse_state["start_x"], mouse_state["end_x"])
            start_y = min(mouse_state["start_y"], mouse_state["end_y"])
            end_y = max(mouse_state["start_y"], mouse_state["end_y"])

            # 画像範囲内へ制限する。
            start_x = max(0, min(start_x, frame_width - 1))
            end_x = max(0, min(end_x, frame_width))
            start_y = max(0, min(start_y, frame_height - 1))
            end_y = max(0, min(end_y, frame_height))

            # 極端に小さいドラッグはROI変更として扱わない。
            if end_x - start_x < 10 or end_y - start_y < 10:
                print("ROI指定が小さすぎるため変更しません。")
                return

            detector.roi_x_range = (
                float(start_x) / float(frame_width),
                float(end_x) / float(frame_width),
            )
            detector.roi_y_range = (
                float(start_y) / float(frame_height),
                float(end_y) / float(frame_height),
            )

            # ROIを変更した場合、以前のキャリブレーション位置は無効。
            detector.reference_cap = None
            detector.angle_history.clear()

            print(f"ROI更新: pixel=({start_x}, {start_y})-({end_x}, {end_y})")
            print(f"ROI更新: x={detector.roi_x_range}, " f"y={detector.roi_y_range}")
            print("ROIを変更したため、c キーで再キャリブレーションしてください。")

    if not detector.start_camera():
        print("カメラの起動に失敗しました。")
    else:
        # WINDOW_NORMALにしてからコールバックを設定する。
        # AUTOSIZEと異なり、OpenCVウィンドウ上で通常のマウス操作ができる。
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 960, 720)
        cv2.setMouseCallback(window_name, mouse_callback)

        print("")
        print("=== CapInspector テスト ===")
        print("ライブ画像上でマウス左ボタンをドラッグ : ROIを指定")
        print("c : 正常に閉じたCAPをキャリブレーション")
        print("o : 開栓後のCAPを判定")
        print("s : 閉栓後のCAPを判定")
        print("q : 終了")
        print("")

        while True:
            ret, frame = detector.cap.read()
            if not ret or frame is None:
                print("カメラの読み込みに失敗しました。")
                break

            display_frame = frame.copy()
            height, width, _ = display_frame.shape
            mouse_state["frame_width"] = width
            mouse_state["frame_height"] = height

            # ROI（注目領域）の設定
            roi_start_x = int(width * detector.roi_x_range[0])
            roi_end_x = int(width * detector.roi_x_range[1])
            roi_start_y = int(height * detector.roi_y_range[0])
            roi_end_y = int(height * detector.roi_y_range[1])

            # ROI視覚化 (青枠)
            cv2.rectangle(
                display_frame,
                (roi_start_x, roi_start_y),
                (roi_end_x, roi_end_y),
                (255, 0, 0),
                2,
            )

            # ROIをドラッグ中の場合は、現在選択中の範囲を黄色枠で表示する。
            if mouse_state["dragging"]:
                cv2.rectangle(
                    display_frame,
                    (mouse_state["start_x"], mouse_state["start_y"]),
                    (mouse_state["end_x"], mouse_state["end_y"]),
                    (0, 255, 255),
                    2,
                )

            # キャリブレーション済みの場合は基準CAP位置を黄色枠で表示する。
            if detector.reference_cap is not None:
                ref_x = int(detector.reference_cap["x"])
                ref_top_y = int(detector.reference_cap["top_y"])
                ref_width = int(detector.reference_cap["width"])
                ref_bottom_y = int(detector.reference_cap["bottom_y"])

                cv2.rectangle(
                    display_frame,
                    (ref_x, ref_top_y),
                    (ref_x + ref_width, ref_bottom_y),
                    (0, 255, 255),
                    2,
                )

            cv2.putText(
                display_frame,
                "Mouse drag: ROI  c:calibrate  o:open  s:closed  q:quit",
                (20, max(30, height - 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

            cv2.imshow(window_name, display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("【停止通知】q キーが押されました。")
                break

            if key == ord("c"):
                print("=== キャリブレーション ===")
                result = detector.calibrate(frame.copy())
                print(f"キャリブレーション結果: {result}")

            if key == ord("o"):
                print("=== 開栓判定 ===")
                detector.mode = "open"
                processed_frame, is_safe, reason = detector.process_frame(frame.copy())
                print(f"OPEN: is_safe={is_safe}, reason={reason}")
                cv2.imshow("Cap Inspector - Result", processed_frame)

            if key == ord("s"):
                print("=== 閉栓判定 ===")
                detector.mode = "closed"
                processed_frame, is_safe, reason = detector.process_frame(frame.copy())
                print(f"CLOSED: is_safe={is_safe}, reason={reason}")
                cv2.imshow("Cap Inspector - Result", processed_frame)

        detector.release()
