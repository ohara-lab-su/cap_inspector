#!/usr/bin/env python
"""赤色キャップの位置・傾斜に基づく開閉検査。"""

import json
import time

import cv2
import numpy as np
from x_logger import XLogger


class CapInspector:
    """赤色キャップの検出・開閉判定を行うクラス。

    Attributes:
        current_mode (str): inspect() の既定判定モード。
        camera_id (int): 画像取得に使用するカメラ番号。

    Notes:
        コンストラクタ引数は初期値であり、個別setterで変更できる。
        is_open() と is_closed() は直近の判定結果だけを返す。
    """

    def __init__(
        self,
        camera_id=0,
        BOTTLE_RIM_Y=275,
        MM_TO_PIXEL=4.0,
        TARGET_CLOSE_MM=0.5,
        TARGET_OPEN_MM=3.5,
        TOLERANCE_MM=1.0,
        current_mode="closed",
        logger=None,
    ):
        self.camera_id = camera_id
        self.BOTTLE_RIM_Y = BOTTLE_RIM_Y
        self.MM_TO_PIXEL = MM_TO_PIXEL
        self.TARGET_CLOSE_MM = TARGET_CLOSE_MM
        self.TARGET_OPEN_MM = TARGET_OPEN_MM
        self.TOLERANCE_MM = TOLERANCE_MM
        self.current_mode = self._normalize_mode(current_mode)
        if logger is None:
            logger = XLogger(logger_name="cap_inspector")
        self.logger = logger
        self.cap = None
        self._reset_detection()
        self._is_safe = None
        self._reason = None
        self._last_frame = None
        self._last_processed_frame = None
        self._validate_parameters(self.get_parameters())

    @staticmethod
    def _normalize_mode(mode):
        if mode == "open":
            return "opened"
        if mode not in ("closed", "opened"):
            raise ValueError("mode must be 'closed' or 'opened' (or legacy 'open')")
        return mode

    @property
    def mode(self):
        return self.current_mode

    @mode.setter
    def mode(self, value):
        self.current_mode = self._normalize_mode(value)

    def _reset_detection(self):
        self._box = None
        self._bottom_points = None
        self._lift_mm = None
        self._tilt_angle = None
        self._aspect_ratio = None
        self._is_tilt_ok = None
        self._result = False
        self._is_open = False
        self._is_closed = False
        self._mode_str = None
        self._detections = []

    def __del__(self):
        try:
            self.stop_camera()
        except Exception:
            pass

    def start_camera(self):
        if self.cap is not None and self.cap.isOpened():
            return True
        self.stop_camera()
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.logger.error(f"Camera open failed: camera_id={self.camera_id}")
            return False
        return True

    def stop_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def release(self):
        self.stop_camera()

    def _read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            if not self.start_camera():
                raise RuntimeError(f"camera open failed: camera_id={self.camera_id}")
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("camera frame read failed")
        return frame

    def _detect_cap(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(
            hsv, lower_red2, upper_red2
        )
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def process_frame(self, frame, current_mode=None):
        """指定したフレームから開栓・閉栓の両条件を判定する。

        Args:
            frame: OpenCV BGR画像。
            current_mode: 返却する判定結果のモード。省略時は現在の設定。

        Returns:
            bool: 指定モードの条件を満たした場合は True。

        Notes:
            開栓・閉栓の判定フラグは同じフレームから同時に更新する。
        """
        mode = self.current_mode
        if current_mode is not None:
            mode = self._normalize_mode(current_mode)
        self._reset_detection()
        self._is_safe = False
        self._reason = "FAIL: Cap not detected"
        self._last_frame = frame.copy()
        self._last_processed_frame = None
        if mode == "closed":
            self._mode_str = f"Closed ({self.TARGET_CLOSE_MM:g}mm)"
        else:
            self._mode_str = f"Opened ({self.TARGET_OPEN_MM:g}mm)"
        for cnt in self._detect_cap(frame):
            if cv2.contourArea(cnt) <= 500:
                continue
            rect = cv2.minAreaRect(cnt)
            box = np.intp(cv2.boxPoints(rect))
            angle = rect[2]
            w, h = rect[1]
            if angle < -45:
                angle += 90
                w, h = h, w
            tilt_angle = abs(angle)
            if h > 0:
                aspect_ratio = w / h
            else:
                aspect_ratio = 0
            is_tilt_ok = tilt_angle < 3.0
            if aspect_ratio < 2.3 or aspect_ratio > 2.8:
                is_tilt_ok = False
            bottom_points = sorted(box, key=lambda p: p[1], reverse=True)[:2]
            cap_bottom_y = (bottom_points[0][1] + bottom_points[1][1]) / 2
            lift_mm = (self.BOTTLE_RIM_Y - cap_bottom_y) / self.MM_TO_PIXEL
            closed_result = bool(
                is_tilt_ok
                and abs(lift_mm - self.TARGET_CLOSE_MM) <= self.TOLERANCE_MM
            )
            open_result = bool(
                is_tilt_ok
                and abs(lift_mm - self.TARGET_OPEN_MM) <= self.TOLERANCE_MM
            )
            if mode == "closed":
                result = closed_result
            else:
                result = open_result
            detection = {
                "box": box.tolist(),
                "bottom_points": [point.tolist() for point in bottom_points],
                "lift_mm": float(lift_mm),
                "tilt_angle": float(tilt_angle),
                "aspect_ratio": float(aspect_ratio),
                "is_tilt_ok": bool(is_tilt_ok),
                "result": result,
                "is_open": open_result,
                "is_closed": closed_result,
            }
            self._detections.append(detection)
            # camera9_2 と同様に全輪郭を処理し、最後の有効輪郭を代表値とする。
            self._box = box
            self._bottom_points = bottom_points
            self._lift_mm = float(lift_mm)
            self._tilt_angle = float(tilt_angle)
            self._aspect_ratio = float(aspect_ratio)
            self._is_tilt_ok = bool(is_tilt_ok)
            self._result = result
            self._is_open = open_result
            self._is_closed = closed_result
            self._is_safe = result
            if not is_tilt_ok:
                self._reason = "FAIL: Cap tilt or aspect ratio"
            elif not result:
                self._reason = "FAIL: Cap position outside tolerance"
            else:
                self._reason = "OK"
        return bool(self._result)

    def inspect(self, current_mode=None):
        """カメラから1フレーム取得して検査する。

        Args:
            current_mode: ``closed`` または ``opened``。省略時は
                インスタンスの現在のモードを使用する。指定時は設定も更新する。

        Returns:
            bool: 指定モードの検査に合格した場合は True。
        """
        if current_mode is not None:
            self.current_mode = self._normalize_mode(current_mode)
        return self.process_frame(self._read_frame())

    def is_open(self) -> bool:
        """直近の検査で開栓条件を満たしたか返す。

        Returns:
            bool: 最後のフレームで開栓条件を満たした場合は True。
                未検査または検出失敗時は False。

        Notes:
            画像の取得や再判定は行わない。inspect() または
            process_frame() で更新された状態を参照する。
        """
        return self._is_open

    def is_closed(self) -> bool:
        """直近の検査で閉栓条件を満たしたか返す。

        Returns:
            bool: 最後のフレームで閉栓条件を満たした場合は True。
                未検査または検出失敗時は False。
        """
        return self._is_closed

    def is_safe(self):
        """直近の指定モードの検査結果を返す。画像取得は行わない。"""
        return self._is_safe

    def get_status(self):
        """直近の検査状態を取得する。再検査は行わない。"""
        return {
            "is_safe": self._is_safe,
            "reason": self._reason,
            "is_open": self._is_open,
            "is_closed": self._is_closed,
        }

    def get_detection(self):
        """直近の代表検出結果をJSON互換の辞書で返す。"""
        if not self._detections:
            return None
        return self._detections[-1].copy()

    def get_detections(self):
        return [item.copy() for item in self._detections]

    def get_bottom_points(self):
        if self._bottom_points is None:
            return None
        return self._bottom_points.tolist()

    def get_box_shape(self):
        if self._box is None:
            return None
        return self._box.tolist()

    def get_lift_mm(self):
        return self._lift_mm

    def get_current_mode(self):
        return self.current_mode

    def get_camera_id(self):
        return self.camera_id

    def get_bottle_rim_y(self):
        return self.BOTTLE_RIM_Y

    def get_mm_to_PIXEL(self):
        return self.MM_TO_PIXEL

    def set_camera_id(self, camera_id):
        self.set_parameters({"camera_id": camera_id})

    def set_bottle_rim_y(self, value):
        self.set_parameters({"BOTTLE_RIM_Y": value})

    def set_mm_to_PIXEL(self, value):
        self.set_parameters({"MM_TO_PIXEL": value})

    def set_target_close_mm(self, value):
        return self.set_parameters({"TARGET_CLOSE_MM": value})

    def set_target_open_mm(self, value):
        return self.set_parameters({"TARGET_OPEN_MM": value})

    def set_tolerance_mm(self, value):
        return self.set_parameters({"TOLERANCE_MM": value})

    def set_mode(self, value):
        return self.set_parameters({"mode": value})

    def _draw_detections(self, frame):
        for detection in self._detections:
            box = np.asarray(detection["box"], dtype=np.intp)
            bottom = detection["bottom_points"]
            cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
            cv2.line(frame, tuple(bottom[0]), tuple(bottom[1]), (0, 255, 255), 3)
            cv2.line(
                frame,
                (0, int(self.BOTTLE_RIM_Y)),
                (frame.shape[1], int(self.BOTTLE_RIM_Y)),
                (255, 255, 0),
                2,
            )
            label = (
                f"[{self._mode_str}] Res:{detection['result']} "
                f"({detection['lift_mm']:.1f}mm)"
            )
            cv2.putText(
                frame, label, (int(box[0][0]), int(box[0][1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2,
            )
        return frame

    def get_image(self, jpeg_quality=85):
        """最新フレームを取得し、判定結果を描画したJPEGを返す。

        Args:
            jpeg_quality: JPEG品質（0～100）。

        Returns:
            dict: ``image``（JPEGバイト列）、``is_safe``、``reason``。

        Notes:
            画像ストリーミングも検査状態を更新する。GUIと制御スクリプトで
            同じインスタンスを共有する場合は、状態更新の競合に注意する。
        """
        frame = self._read_frame()
        self.process_frame(frame)
        processed = self._draw_detections(frame.copy())
        self._last_processed_frame = processed.copy()
        ok, encoded = cv2.imencode(
            ".jpg", processed, [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]
        )
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        return {
            "image": encoded.tobytes(),
            "is_safe": bool(self._is_safe),
            "reason": self._reason,
        }

    def image_stream(self, jpeg_quality=85, interval_sec=0.1):
        try:
            while True:
                yield self.get_image(jpeg_quality=jpeg_quality)
                if interval_sec > 0:
                    time.sleep(float(interval_sec))
        except GeneratorExit:
            raise

    def get_parameters(self):
        return {
            "camera_id": self.camera_id,
            "BOTTLE_RIM_Y": self.BOTTLE_RIM_Y,
            "MM_TO_PIXEL": self.MM_TO_PIXEL,
            "TARGET_CLOSE_MM": self.TARGET_CLOSE_MM,
            "TARGET_OPEN_MM": self.TARGET_OPEN_MM,
            "TOLERANCE_MM": self.TOLERANCE_MM,
            "mode": self.current_mode,
        }

    @classmethod
    def _validate_parameters(cls, parameters):
        cls._normalize_mode(parameters["mode"])
        if float(parameters["MM_TO_PIXEL"]) <= 0:
            raise ValueError("MM_TO_PIXEL must be positive")
        if float(parameters["TOLERANCE_MM"]) < 0:
            raise ValueError("TOLERANCE_MM must be nonnegative")

    def set_parameters(self, parameters):
        """画像認識パラメータを一括更新する。

        Args:
            parameters (dict): 更新対象のパラメータ辞書。指定しない値は維持する。

        Returns:
            dict: 更新後の全パラメータ。

        Raises:
            ValueError: 未知のキー、または不正な設定値を受け取った場合。
        """
        aliases = {"current_mode": "mode"}
        allowed = set(self.get_parameters())
        normalized = {}
        for key, value in parameters.items():
            normalized_key = aliases.get(key, key)
            normalized[normalized_key] = value
        unknown = set(normalized) - allowed
        if unknown:
            raise ValueError(f"unknown parameters: {sorted(unknown)}")
        new = self.get_parameters()
        new.update(normalized)
        new["camera_id"] = int(new["camera_id"])
        new["BOTTLE_RIM_Y"] = int(new["BOTTLE_RIM_Y"])
        for key in ("MM_TO_PIXEL", "TARGET_CLOSE_MM", "TARGET_OPEN_MM", "TOLERANCE_MM"):
            new[key] = float(new[key])
        new["mode"] = self._normalize_mode(new["mode"])
        self._validate_parameters(new)
        camera_changed = new["camera_id"] != self.camera_id
        if camera_changed:
            self.stop_camera()
        for key, value in new.items():
            if key == "mode":
                self.current_mode = value
            else:
                setattr(self, key, value)
        return self.get_parameters()

    def save_parameters(self, filename):
        parameters = self.get_parameters()
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(parameters, file, ensure_ascii=False, indent=2)
        return parameters

    def load_parameters(self, filename):
        with open(filename, "r", encoding="utf-8") as file:
            parameters = json.load(file)
        return self.set_parameters(parameters)

    def run(self):
        """camera9_2 と同等のキー操作・描画によるローカルテスト。"""
        current_mode = "closed"
        if not self.start_camera():
            raise RuntimeError(f"camera open failed: camera_id={self.camera_id}")
        print("=== 操作方法 ===")
        print("'c' キー: 閉まっているかの判定モード (0.5mm) に切替")
        print("'o' キー: 開いているかの判定モード (4.0mm) に切替")
        print("'q' キー: 終了")
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    break
                self.process_frame(frame, current_mode)
                self._draw_detections(frame)
                cv2.imshow("Webカメラ映像", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("c"):
                    current_mode = "closed"
                    print("-> 【閉まっているか】の判定モード (0.5mm) に切り替えました")
                elif key == ord("o"):
                    current_mode = "opened"
                    print("-> 【開いているか】の判定モード (4.0mm) に切り替えました")
        finally:
            self.stop_camera()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    CapInspector().run()
