# 完成版
import cv2
import numpy as np
from x_logger import XLogger

class CapInspector:
    def __init__(
        self,
        camera_id = 0,
        BOTTLE_RIM_Y = 275,
        # ↑画面上の「透明の瓶のくぼんでいる線」のY座標（ピクセル）、今の設定より、BOTTLE_RIM_Yの位置を上にしたい場合は数値を小さく、下にしたい場合は大きくする。
        MM_TO_PIXEL = 4.0,       # 1mm が何ピクセルに相当するか（実際の距離感に合わせて調整）
        TARGET_CLOSE_MM = 0.5,   # 目標の高さ（ミリメートル）
        TARGET_OPEN_MM = 3.5,    # 目標の高さ（ミリメートル）
        TOLERANCE_MM = 1.0,      # 許容する誤差（ミリメートル)
        current_mode = "closed",      #初期モードの設定 ("closed" または "opened")
        logger = None,
    ):
        """カメラと検出パラメータの初期化"""
        self.camera_id = camera_id
        self.BOTTLE_RIM_Y = BOTTLE_RIM_Y
        self.MM_TO_PIXEL = MM_TO_PIXEL
        self.TARGET_CLOSE_MM = TARGET_CLOSE_MM
        self.TARGET_OPEN_MM = TARGET_OPEN_MM
        self.TOLERANCE_MM = TOLERANCE_MM
        self.current_mode = current_mode

        if logger is not None:
            self.logger = logger
        else:
            self.logger = XLogger(logger_name="cap_inspector")

        self.logger.info(
            f"CapInspector initialized: camera_id={self.camera_id}, "
            f"BOTTLE_RIM_Y={self.BOTTLE_RIM_Y}, MM_TO_PIXEL={self.MM_TO_PIXEL}, "
            f"TARGET_CLOSE_MM={self.TARGET_CLOSE_MM}, TARGET_OPEN_MM={self.TARGET_OPEN_MM}, "
            f"TOLERANCE_MM={self.TOLERANCE_MM}, current_mode={self.current_mode}"
        )

    def __del__(self):
        """デストラクタでリソースを解放する。"""
        try:
            self.release()
        except Exception:
            pass

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def set_camera_id(self, camera_id):
        self.camera_id = camera_id

    def set_bottle_rim_y(self, value):
        self.BOTTLE_RIM_Y = value

    def set_mm_to_PIXEL(self, value):
        self.MM_TO_PIXEL = value

    def get_camera_id(self):
        return self.camera_id

    def get_bottle_rim_y(self):
        return self.BOTTLE_RIM_Y

    def get_mm_to_PIXEL(self):
        return self.MM_TO_PIXEL

    def get_bottom_points(self):
        return self._bottom_points

    def get_lift_mm(self):
        return self._lift_mm

    # def get_frame_shape(self):
    #      return self.frame.shape[1]

    def get_box_shape(self):
        return self._box

    def get_current_mode(self):
        return self.current_mode

    #
    # コアメソッド
    #

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

    def _read_frame(self):
        """カメラから1フレーム取得する。未起動なら自動的に開始する。"""
        if self.cap is None or not self.cap.isOpened():
            if not self.start_camera():
                raise RuntimeError(f"camera open failed: camera_id={self.camera_id}")
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("camera frame read failed")
        return frame

    def _detect_cap(self, frame):
        """
        赤色キャップを認識して領域を取得する

        Args:
            frame:

        Returns:

        """
        # 1. BGR画像からHSV色空間に変換
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 2. 赤色の範囲を定義
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 | mask2

        # ノイズ除去
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 3. 赤色の領域の輪郭を検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def inspect(self, current_mode: str):
        """現在の1フレームを判定し、判定状態を更新する。"""
        frame = self._read_frame()
        result = self.process_frame(frame)
        # self._is_safe = bool(is_safe)
        # self._reason = reason
        # self.logger.debug(
        #     f"Inspection completed: is_safe={self._is_safe}, reason={self._reason}"
        # )
        # return self._is_safe
        return result

    def process_frame(
            self,
            frame,
            current_mode: str,
    ):
        """
        判定のコアルーチン
        フレームに対して判定する

        Args:
            current_mode:
            closed: 閉まっているかの判定モード (0.5mm) に切替")
            opened: 開いているかの判定モード (4.0mm) に切替")

        Returns:
        """

        # ret, self.frame = self.cap.read()
        # if not ret:
        #     exit()

        contours = self._detect_cap(frame)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                # 最小外接矩形を取得
                rect = cv2.minAreaRect(cnt)
                self._box = cv2.boxPoints(rect)
                self._box = np.intp(self._box)

                # 角度とサイズ（幅・高さ）の取得
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

                # 水平判定（3度未満かつアスペクト比が正常）
                is_tilt_ok = (tilt_angle < 3.0) and (2.3 <= aspect_ratio <= 2.8)

                # 蓋の底面（黄色い線）のY座標を特定
                sorted_box = sorted(self._box, key=lambda p: p[1], reverse=True)
                self._bottom_points = sorted_box[:2]
                cap_bottom_y = (self._bottom_points[0][1] + self._bottom_points[1][1]) / 2

                # 瓶のくぼみからふたの底面までのピクセル差を計算し、mmに換算
                lift_px = self.BOTTLE_RIM_Y - cap_bottom_y
                self._lift_mm = lift_px / self.MM_TO_PIXEL

                # --- モードに応じた判定 ---
                if current_mode == "closed":
                    diff = abs(self._lift_mm - self.TARGET_CLOSE_MM)
                    self._result = is_tilt_ok and (diff <= self.TOLERANCE_MM)
                    self._mode_str = "Closed (0.5mm)"

                elif current_mode == "opened":
                    diff = abs(self._lift_mm - self.TARGET_OPEN_MM)
                    self._result = is_tilt_ok and (diff <= self.TOLERANCE_MM)
                    self._mode_str = "Opened (3.5mm)"

                return self._result

    def run(self):
        """
        無限ループ系、動作テスト用
        Returns:

        """
        current_mode = "closed"

        # カメラを初期化
        self.start_camera()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                exit()

            result = self.process_frame(frame, current_mode)

            # 範囲の確認のための仕組み（このメソッドでは使わない）
            # 画面に描画
            cv2.drawContours(frame, [self._box], 0, (0, 255, 0), 2)
            cv2.line(
                frame,
                tuple(self._bottom_points[0]),
                tuple(self._bottom_points[1]),
                (0, 255, 255),
                3,
            )
            # 基準の瓶のくぼみライン（水色）
            cv2.line(
                frame,
                (0, self.BOTTLE_RIM_Y),
                (frame.shape[1], self.BOTTLE_RIM_Y),
                (255, 255, 0),
                2,
            )

            # テキスト表示（現在のモードと判定結果、実測のmmを表示）
            text = f"[{self._mode_str}] Res:{self._result} ({self._lift_mm:.1f}mm)"
            cv2.putText(
                frame,
                text,
                (self._box[0][0], self._box[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

            # 映像を表示
            cv2.imshow("Webカメラ映像", frame)

            # キー入力を待機
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                current_mode = "closed"
                print("-> 【閉まっているか】の判定モード (0.5mm) に切り替えました")
            elif key == ord("o"):
                current_mode = "opened"
                print("-> 【開いているか】の判定モード (4.0mm) に切り替えました")

        # self.cap.release()
        # cv2.destroyAllWindows()


if __name__ == '__main__':
    cap = CapInspector()
    cap.run()