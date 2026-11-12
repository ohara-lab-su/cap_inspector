#完成版
import cv2
import numpy as np

# カメラを初期化
cap = cv2.VideoCapture(0)

# ---基準値の設定 ---
# 画面上の「透明の瓶のくぼんでいる線」のY座標（ピクセル）
# 今の設定より、BOTTLE_RIM_Yの位置を上にしたい場合は数値を小さく、下にしたい場合は大きくする。
BOTTLE_RIM_Y = 275

# 1mm が何ピクセルに相当するか（実際の距離感に合わせて調整）
MM_TO_PIXEL = 4.0

# 目標の高さ（ミリメートル）
TARGET_CLOSE_MM = 0.5  # 閉まっているとき
TARGET_OPEN_MM = 3.5  # 開いているとき

# 許容する誤差（ミリメートル）
TOLERANCE_MM = 1.0

# 初期モードの設定 ("closed" または "opened")
current_mode = "closed"

print("=== 操作方法 ===")
print("'c' キー: 閉まっているかの判定モード (0.5mm) に切替")
print("'o' キー: 開いているかの判定モード (4.0mm) に切替")
print("'q' キー: 終了")

while True:
    ret, frame = cap.read()
    if not ret:
        break

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

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:
            # 最小外接矩形を取得
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.intp(box)

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
            sorted_box = sorted(box, key=lambda p: p[1], reverse=True)
            bottom_points = sorted_box[:2]
            cap_bottom_y = (bottom_points[0][1] + bottom_points[1][1]) / 2

            # 瓶のくぼみからふたの底面までのピクセル差を計算し、mmに換算
            lift_px = BOTTLE_RIM_Y - cap_bottom_y
            lift_mm = lift_px / MM_TO_PIXEL

            # --- モードに応じた判定 ---
            if current_mode == "closed":
                diff = abs(lift_mm - TARGET_CLOSE_MM)
                result = is_tilt_ok and (diff <= TOLERANCE_MM)
                mode_str = "Closed (0.5mm)"
            else:
                diff = abs(lift_mm - TARGET_OPEN_MM)
                result = is_tilt_ok and (diff <= TOLERANCE_MM)
                mode_str = "Opened (3.5mm)"

            # 画面に描画
            cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
            cv2.line(
                frame,
                tuple(bottom_points[0]),
                tuple(bottom_points[1]),
                (0, 255, 255),
                3,
            )
            # 基準の瓶のくぼみライン（水色）
            cv2.line(
                frame,
                (0, BOTTLE_RIM_Y),
                (frame.shape[1], BOTTLE_RIM_Y),
                (255, 255, 0),
                2,
            )

            # テキスト表示（現在のモードと判定結果、実測のmmを表示）
            text = f"[{mode_str}] Res:{result} ({lift_mm:.1f}mm)"
            cv2.putText(
                frame,
                text,
                (box[0][0], box[0][1] - 10),
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

cap.release()
cv2.destroyAllWindows()
