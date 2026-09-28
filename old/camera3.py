# ---背景を黒とした時に瓶が傾いているのかをみる（照明は無し）-----
from collections import deque
import math
import cv2
import numpy as np


class CapDetector:

    def __init__(
        self,
        camera_id=1,
        roi_ratio=0.40,
        threshold_val=210,  # 瓶の反射を弾くため、白閾値を少し高めに設定
        angle_limit=3.0,  # 許容角度（3度以上で停止）
        min_aspect_ratio=1.9,  # 1.9未満はキャップの「浮き・傾き」と判定
        min_area=800,
        smooth_frames=3,
    ):
        """カメラと検出パラメータの初期化"""
        self.camera_id = camera_id
        self.roi_ratio = roi_ratio
        self.threshold_val = threshold_val
        self.angle_limit = angle_limit
        self.min_aspect_ratio = min_aspect_ratio
        self.min_area = min_area
        self.cap = None
        self.angle_history = deque(maxlen=smooth_frames)

    def start_camera(self):
        """カメラの開始"""
        self.cap = cv2.VideoCapture(self.camera_id)
        return self.cap.isOpened()

    def process_frame(self, frame):
        """1フレームあたりのキャップ検出と判定処理"""
        height, width, _ = frame.shape
        roi_limit_y = int(height * self.roi_ratio)
        roi = frame[0:roi_limit_y, 0:width]

        # 二値化とノイズ除去
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)
        _, thresh = cv2.threshold(
            blurred_roi, self.threshold_val, 255, cv2.THRESH_BINARY
        )

        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # 輪郭検出
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            if cv2.contourArea(cnt) < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            if h == 0:
                continue

            # 1. アスペクト比判定 (片側が浮いて傾くと枠の高さhが増えて比率が低下する)
            aspect_ratio = float(w) / h
            if aspect_ratio < self.min_aspect_ratio:
                error_msg = f"STOP: Gap/Tilt Detected (Aspect: {aspect_ratio:.2f} < {self.min_aspect_ratio:.2f})"
                self._draw_stop_message(frame, error_msg)
                return frame, False, error_msg

            # 2. キャップ輪郭自体の回転角度（最小外接矩形）を取得
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (w_r, h_r), rect_angle = rect

            if w_r == 0 or h_r == 0:
                continue

            # 長辺と短辺に基づく角度補正
            if w_r < h_r:
                calc_angle = abs(rect_angle)
            else:
                calc_angle = abs(rect_angle - 90)

            if calc_angle > 45:
                calc_angle = abs(90 - calc_angle)

            # 角度の平滑化（チラつき防止）
            self.angle_history.append(calc_angle)
            smoothed_angle = sum(self.angle_history) / len(self.angle_history)

            # 3. 角度による判定（制限角度以上で停止）
            if smoothed_angle >= self.angle_limit:
                error_msg = (
                    f"STOP: Angle {smoothed_angle:.1f} deg >= {self.angle_limit} deg"
                )
                self._draw_stop_message(frame, error_msg)
                return frame, False, error_msg

            # 正常時の描画処理
            bottom_y = y + h
            cv2.putText(
                frame,
                f"Angle: {smoothed_angle:.1f} deg | Aspect: {aspect_ratio:.2f}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
            cv2.rectangle(frame, (x, y), (x + w, bottom_y), (0, 255, 0), 2)
            cv2.line(frame, (x, bottom_y), (x + w, bottom_y), (0, 0, 255), 3)

        return frame, True, None

    def _draw_stop_message(self, frame, message):
        """停止時の警告メッセージ描画"""
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
        """メインループの実行"""
        if not self.start_camera():
            print("カメラの起動に失敗しました。")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            processed_frame, is_safe, reason = self.process_frame(frame)
            cv2.imshow("Webcam - White Cap Detection", processed_frame)

            # 傾きを検知した場合は処理停止
            if not is_safe:
                print(f"【停止通知】{reason}")
                cv2.waitKey(2000)
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.release()

    def release(self):
        """リソースの解放"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()


# --- 実行用コード ---
if __name__ == "__main__":
    detector = CapDetector(
        camera_id=1,  # カメラ番号
        angle_limit=3.0,  # 許容角度（3度）
        min_aspect_ratio=1.9,  # アスペクト比閾値（1.9未満で傾き停止）
        threshold_val=210,  # 瓶の光反射を消すための二値化閾値
    )
    detector.run()

# import math
# import cv2
# import numpy as np
#
#
# class CapInspector:
#
#     def __init__(
#         self,
#         camera_id=1,
#         roi_ratio=0.40,
#         threshold_val=190,
#         angle_limit=3.0,
#         min_area=800,
#     ):
#         """カメラと検出パラメータの初期化"""
#         self.camera_id = camera_id
#         self.roi_ratio = roi_ratio  # 画面上部からの割合
#         self.threshold_val = threshold_val  # 二値化の閾値
#         self.angle_limit = angle_limit  # 許容する傾き角度（度）
#         self.min_area = min_area  # 最小輪郭面積
#         self.cap = None
#
#     def start_camera(self):
#         """カメラの開始"""
#         self.cap = cv2.VideoCapture(self.camera_id)
#         return self.cap.isOpened()
#
#     def process_frame(self, frame):
#         """1フレームあたりのキャップ検出と判定処理"""
#         height, width, _ = frame.shape
#         roi_limit_y = int(height * self.roi_ratio)
#         roi = frame[0:roi_limit_y, 0:width]
#
#         # 二値化とノイズ除去
#         gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
#         _, thresh = cv2.threshold(gray_roi, self.threshold_val, 255, cv2.THRESH_BINARY)
#         kernel = np.ones((3, 3), np.uint8)
#         thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
#
#         # 輪郭検出
#         contours, _ = cv2.findContours(
#             thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
#         )
#
#         for cnt in contours:
#             if cv2.contourArea(cnt) < self.min_area:
#                 continue
#
#             # 最小外接矩形の頂点を取得
#             rect = cv2.minAreaRect(cnt)
#             box = cv2.boxPoints(rect)
#             box = np.int32(box)
#
#             # Y座標でソートして上側の左右2点を抽出
#             pts_by_y = sorted(box, key=lambda p: p[1])
#             top_two = sorted(pts_by_y[:2], key=lambda p: p[0])
#             bottom_two = sorted(pts_by_y[2:], key=lambda p: p[0])
#
#             p_tl, p_tr = top_two[0], top_two[1]
#             p_bl = bottom_two[0]
#
#             # 比率チェック（アスペクト比）
#             width_box = math.hypot(p_tr[0] - p_tl[0], p_tr[1] - p_tl[1])
#             height_box = math.hypot(p_bl[0] - p_tl[0], p_bl[1] - p_tl[1])
#
#             if height_box == 0:
#                 continue
#
#             aspect_ratio = width_box / height_box
#
#             if 1.5 <= aspect_ratio <= 4.0:
#                 # 角度計算（水平0度からの傾き）
#                 dx = p_tr[0] - p_tl[0]
#                 dy = p_tr[1] - p_tl[1]
#                 angle_rad = math.atan2(dy, dx)
#                 angle = abs(math.degrees(angle_rad))
#
#                 if angle > 45:
#                     angle = abs(90 - angle)
#
#                 # 判定：制限角度以上の場合
#                 if angle >= self.angle_limit:
#                     cv2.putText(
#                         frame,
#                         f"STOP: Angle {angle:.1f} deg >= {self.angle_limit} deg",
#                         (30, 50),
#                         cv2.FONT_HERSHEY_SIMPLEX,
#                         0.8,
#                         (0, 0, 255),
#                         2,
#                     )
#                     return frame, False, angle  # is_safe = False
#
#                 # 正常時の描画処理
#                 x, y, w, h = cv2.boundingRect(cnt)
#                 bottom_y = y + h
#
#                 cv2.putText(
#                     frame,
#                     f"Angle: {angle:.1f} deg",
#                     (x, max(20, y - 10)),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     0.6,
#                     (0, 255, 0),
#                     2,
#                 )
#                 cv2.rectangle(frame, (x, y), (x + w, bottom_y), (0, 255, 0), 2)
#                 cv2.line(frame, (x, bottom_y), (x + w, bottom_y), (0, 0, 255), 3)
#
#         return frame, True, None  # is_safe = True
#
#     def run(self):
#         """メインループの実行"""
#         if not self.start_camera():
#             print("カメラの起動に失敗しました。")
#             return
#
#         while True:
#             ret, frame = self.cap.read()
#             if not ret:
#                 break
#
#             processed_frame, is_safe, angle = self.process_frame(frame)
#
#             cv2.imshow("Webcam - White Cap Detection", processed_frame)
#
#             # 限界角度を超えた場合は停止処理
#             if not is_safe:
#                 print(
#                     f"【停止】キャップが {angle:.1f} 度傾いたため（{self.angle_limit}度以上）処理を停止します。"
#                 )
#                 cv2.waitKey(2000)
#                 break
#
#             if cv2.waitKey(1) & 0xFF == ord("q"):
#                 break
#
#         self.release()
#
#     def release(self):
#         """リソースの解放"""
#         if self.cap:
#             self.cap.release()
#         cv2.destroyAllWindows()
#
#
# # --- 実行用コード ---
# if __name__ == "__main__":
#     # クラスのインスタンス化（必要に応じて閾値や許容角度を変更可能）
#     detector = CapInspector(
#         camera_id=1,  # カメラ番号
#         angle_limit=5.0,  # 許容する傾き角度（3度）
#         threshold_val=190,  # 白二値化の閾値
#     )
#
#     # 実行
#     detector.run()
