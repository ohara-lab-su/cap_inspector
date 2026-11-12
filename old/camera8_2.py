# import cv2
# import numpy as np
#
# # カメラを初期化
# cap = cv2.VideoCapture(0)
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     # 1. BGR画像からHSV色空間に変換
#     hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
#
#     # 2. 赤色の範囲を定義
#     lower_red1 = np.array([0, 120, 70])
#     upper_red1 = np.array([10, 255, 255])
#     lower_red2 = np.array([170, 120, 70])
#     upper_red2 = np.array([180, 255, 255])
#
#     # マスク画像の作成
#     mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
#     mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
#     mask = mask1 | mask2
#
#     # ノイズ除去
#     kernel = np.ones((5, 5), np.uint8)
#     mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
#     mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
#
#     # 3. 赤色の領域の輪郭を検出
#     contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     for cnt in contours:
#         area = cv2.contourArea(cnt)
#         if area > 500:  # 面積のしきい値
#             # --- 傾きを計算できる最小外接矩形を取得 ---
#             # rect = ((center_x, center_y), (width, height), angle)
#             rect = cv2.minAreaRect(cnt)
#             box = cv2.boxPoints(rect)
#             box = np.intp(box)  # OpenCVの描画用に整数へ変換
#
#             # 角度の正規化（OpenCVの仕様によるブレを補正して水平からのズレ角度を計算）
#             angle = rect[2]
#             w, h = rect[1]
#             if w < h:
#                 angle = angle + 90
#
#             # 水平からの傾き角度（絶対値）
#             tilt_angle = abs(angle)
#             if tilt_angle > 45:
#                 tilt_angle = abs(90 - tilt_angle)
#
#             # --- 3度以上傾いているかでTrue / Falseを判定 ---
#             is_horizontal = tilt_angle < 3.0
#
#             # 判定結果をコンソールに出力
#             print(f"傾き角度: {tilt_angle:.2f}度 -> 判定: {is_horizontal}")
#
#             # --- 描画処理 ---
#             # 全体を緑色の枠線で囲む（最小外接矩形の枠）
#             cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
#
#             # 蓋の底部分（傾きに合わせた底側の2点）に黄色い線を引く
#             # boxの並び順（左下、左上、右上、右下など）から底面にあたる辺を特定して線を引く
#             # ここでは簡易的に、boxの座標のうちy座標が大きい下側の2点をつなぐ
#             sorted_box = sorted(box, key=lambda p: p[1], reverse=True)
#             bottom_points = sorted_box[:2]  # yが大きい（下側の）2点
#             cv2.line(
#                 frame,
#                 tuple(bottom_points[0]),
#                 tuple(bottom_points[1]),
#                 (0, 255, 255),
#                 3,
#             )
#
#             # 画面にTrue/Falseのテキストを表示
#             text = f"Status: {is_horizontal} ({tilt_angle:.1f}deg)"
#             cv2.putText(
#                 frame,
#                 text,
#                 (box[0][0], box[0][1] - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.6,
#                 (0, 255, 0),
#                 2,
#             )
#
#     # 映像を表示
#     cv2.imshow("Webカメラ映像", frame)
#
#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break
#
# cap.release()
# cv2.destroyAllWindows()

# 地面に対して水平な場合にTrue、左右前後に傾いた場合にはFalseを返すように設定（赤い蓋）
import cv2
import numpy as np

# カメラを初期化
cap = cv2.VideoCapture(0)

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

    # マスク画像の作成
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
        if area > 500:  # 面積のしきい値
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

            # アスペクト比の計算
            if h > 0:
                aspect_ratio = w / h
            else:
                aspect_ratio = 0

            # --- （AR: 2.53付近）がTrueになる範囲に調整 ---
            is_aspect_ok = 2.3 <= aspect_ratio <= 2.8

            # 左右の傾き（3度未満） AND アスペクト比が正常範囲内
            is_horizontal = (tilt_angle < 3.0) and is_aspect_ok

            # 判定結果をコンソールに出力
            print(
                f"傾き角度: {tilt_angle:.2f}度, アスペクト比: {aspect_ratio:.2f} ->"
                f" 判定: {is_horizontal}"
            )

            # --- 描画処理 ---
            cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)

            sorted_box = sorted(box, key=lambda p: p[1], reverse=True)
            bottom_points = sorted_box[:2]
            cv2.line(
                frame,
                tuple(bottom_points[0]),
                tuple(bottom_points[1]),
                (0, 255, 255),
                3,
            )

            # 画面にTrue/Falseのテキストを表示
            text = (
                f"Status: {is_horizontal} (Ang:{tilt_angle:.1f}, AR:{aspect_ratio:.2f})"
            )
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

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
