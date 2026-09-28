from collections import deque
import math
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
        angle_limit=3.0,  # 許容角度（度）
        threshold_val=210,
        min_aspect_ratio=1.9,  # 1.9未満で傾き・浮き検知
        smooth_frames=3,
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
        self.logger = logger if logger is not None else XLogger(logger_name="cap_inspector")
        self.logger.info(
            f"CapInspector initialized: camera_id={self.camera_id}, "
            f"roi_x_range={self.roi_x_range}, roi_y_range={self.roi_y_range}, "
            f"angle_limit={self.angle_limit}, threshold_val={self.threshold_val}, "
            f"min_aspect_ratio={self.min_aspect_ratio}, smooth_frames={self.smooth_frames}"
        )

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

    def process_frame(self, frame):
        """1フレームあたりのキャップ検出と傾き判定"""
        height, width, _ = frame.shape

        # 1. ROI（注目領域）の設定
        roi_start_x = int(width * self.roi_x_range[0])
        roi_end_x = int(width * self.roi_x_range[1])
        roi_start_y = int(height * self.roi_y_range[0])
        roi_end_y = int(height * self.roi_y_range[1])

        roi = frame[roi_start_y:roi_end_y, roi_start_x:roi_end_x]
        roi_h, roi_w, _ = roi.shape
        roi_center_x = roi_w / 2.0

        # 青色ガイド枠の描画（ROI視覚化）
        cv2.rectangle(
            frame,
            (roi_start_x, roi_start_y),
            (roi_end_x, roi_end_y),
            (255, 0, 0),
            1,
        )

        # 2. HSVによる白の抽出（V>=210で厳しく判定）
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, self.threshold_val])
        upper_white = np.array([180, 30, 255])
        thresh = cv2.inRange(hsv_roi, lower_white, upper_white)

        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # 3. 輪郭検出とターゲット抽出
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        valid_caps = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 800:
                continue

            rx, ry, rw, rh = cv2.boundingRect(cnt)
            if rh == 0:
                continue

            aspect_ratio = float(rw) / rh

            # アスペクト比1.5〜4.0 ＆ ROI中央付近（20%以内）の条件チェック
            if 1.5 <= aspect_ratio <= 4.0:
                cnt_center_x = rx + (rw / 2.0)
                dist_from_center = abs(cnt_center_x - roi_center_x)
                if dist_from_center < (roi_w * 0.20):
                    valid_caps.append((area, cnt, rx, ry, rw, rh))

        # 候補がない場合（キャップが映っていない状態）
        if not valid_caps:
            return frame, True, None

        # 4. 最も大きな白オブジェクト（本物のキャップ）を選択
        valid_caps.sort(key=lambda item: item[0], reverse=True)
        _, best_cnt, rx, ry, rw, rh = valid_caps[0]

        # ROI内から画面全体の絶対座標への変換
        abs_x = roi_start_x + rx
        abs_y = roi_start_y + ry
        abs_bottom_y = abs_y + rh

        # --- A. アスペクト比判定 (片側が浮くと枠の高さが増えて比率が下がる) ---
        aspect_ratio = float(rw) / rh
        if aspect_ratio < self.min_aspect_ratio:
            error_msg = f"STOP: Gap/Tilt Detected (Aspect: {aspect_ratio:.2f} < {self.min_aspect_ratio:.2f})"
            self._draw_stop_message(frame, error_msg)
            return frame, False, error_msg

        # --- B. 最小外接矩形による回転角度判定 ---
        rect = cv2.minAreaRect(best_cnt)
        (cx, cy), (w_r, h_r), rect_angle = rect

        if w_r > 0 and h_r > 0:
            if w_r < h_r:
                calc_angle = abs(rect_angle)
            else:
                calc_angle = abs(rect_angle - 90)

            if calc_angle > 45:
                calc_angle = abs(90 - calc_angle)
        else:
            calc_angle = 0.0

        # 角度の平滑化（平均化）
        self.angle_history.append(calc_angle)
        smoothed_angle = sum(self.angle_history) / len(self.angle_history)

        # 限界角度オーバー判定
        if smoothed_angle >= self.angle_limit:
            error_msg = f"STOP: Angle {smoothed_angle:.1f} deg >= {self.angle_limit} deg"
            self._draw_stop_message(frame, error_msg)
            return frame, False, error_msg

        # 正常時の描画処理
        cv2.putText(
            frame,
            f"Angle: {smoothed_angle:.1f} deg | Aspect: {aspect_ratio:.2f}",
            (abs_x, max(20, abs_y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )
        cv2.rectangle(frame, (abs_x, abs_y), (abs_x + rw, abs_bottom_y), (0, 255, 0), 2)
        cv2.line(
            frame,
            (abs_x, abs_bottom_y),
            (abs_x + rw, abs_bottom_y),
            (0, 255, 255),
            3,
        )

        return frame, True, None


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
        }

    def set_parameters(self, parameters):
        """認識パラメータをまとめて更新する。既存キーのみ受け付ける。"""
        self.logger.info(f"Parameter update requested: {parameters}")
        allowed = {
            "camera_id", "roi_x_range", "roi_y_range", "angle_limit",
            "threshold_val", "min_aspect_ratio", "smooth_frames",
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
            self.angle_history = deque(self.angle_history, maxlen=self.smooth_frames)
        current = self.get_parameters()
        self.logger.info(f"Parameters updated: {current}")
        return current

    def get_status(self):
        """現在の1フレームを判定し、is_safe と reason を返す。"""
        frame = self._read_frame()
        _, is_safe, reason = self.process_frame(frame)
        self.logger.debug(f"Inspection status: is_safe={bool(is_safe)}, reason={reason}")
        return {"is_safe": bool(is_safe), "reason": reason}

    def get_image(self, jpeg_quality=85):
        """現在の認識結果を描画したJPEG画像を bytes で返す。"""
        frame = self._read_frame()
        processed_frame, is_safe, reason = self.process_frame(frame)
        ok, encoded = cv2.imencode(
            ".jpg", processed_frame,
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
            f"Image stream started: jpeg_quality={jpeg_quality}, interval_sec={interval_sec}"
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
                break

            processed_frame, is_safe, reason = self.process_frame(frame)
            cv2.imshow("Webcam - White Cap Detection", processed_frame)

            # 傾きを検知した場合に処理停止
            if not is_safe:
                print(f"【停止通知】{reason}")
                cv2.waitKey(2000)
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.release()

    def release(self):
        """リソースの解放"""
        self.logger.info("CapInspector release requested")
        if self.cap:
            self.cap.release()
            self.cap = None
            self.logger.info("Camera released")
        cv2.destroyAllWindows()
        self.logger.info("CapInspector released")


# --- 実行用コード ---
if __name__ == "__main__":
    logger = XLogger()
    detector = CapInspector(
        camera_id=0,
        angle_limit=3.0,  # 許容角度（3度以上で停止）
        min_aspect_ratio=1.9,  # アスペクト比1.9未満（高さ増加）で停止
        threshold_val=210,  # 瓶の光反射を消すための二値化閾値
        logger=logger,
    )

    detector.run()
