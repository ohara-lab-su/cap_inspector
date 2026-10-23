# import cv2
# import numpy as np
#
# cap = cv2.VideoCapture(0)
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (7, 7), 0)
#
#     # 1. Cannyエッジ検出で輪郭（白線）を抽出
#     edges = cv2.Canny(blurred, 50, 150)
#     edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
#
#     # 2. エッジ（白ピクセル）の座標をすべて取得
#     y_indices, x_indices = np.where(edges > 0)
#
#     if len(y_indices) > 0:
#         # 画面内にある「最も上のエッジ」のy座標を蓋の上線とする
#         top_y = np.min(y_indices)
#
#         # 上部付近（一番上の線から少し下の範囲）にあるx座標から、蓋の左右の幅を割り出す
#         mask_top = (y_indices >= top_y) & (y_indices <= top_y + 40)
#         if np.any(mask_top):
#             x_in_top = x_indices[mask_top]
#             left_x = np.min(x_in_top)
#             right_x = np.max(x_in_top)
#
#             # --- 【調整ポイント】 ---
#             # 1cm程度下に降りた位置（くぼみ）までの高さをピクセル数で指定します
#             # 映像を見ながら、この数値（例: 35 や 40 など）を増やしたり減らしたりして調整してください
#             lid_height = 50
#
#             # 赤い枠の四隅の座標を決定
#             # 左右は少しだけ余裕（マージン）を持たせています
#             pt1 = (left_x - 3, top_y)
#             pt2 = (right_x + 3, top_y + lid_height)
#
#             # 3. 黒背景のエッジ画像の上に赤い長方形を描画
#             cv2.rectangle(edges_colored, pt1, pt2, (0, 0, 255), 2)
#             cv2.putText(
#                 edges_colored,
#                 "Lid",
#                 (pt1[0], top_y - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.7,
#                 (0, 0, 255),
#                 2,
#             )
#
#     # 4. 画面に表示
#     cv2.imshow("Webカメラ映像 (蓋の赤枠指定)", edges_colored)
#
#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break
#
# cap.release()
# cv2.destroyAllWindows()
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # 1. Cannyエッジ検出で輪郭（白線）を抽出
    edges = cv2.Canny(blurred, 50, 150)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    y_indices, x_indices = np.where(edges > 0)

    if len(y_indices) > 0:
        # 画面内にある「最も上のエッジ」のy座標
        top_y = np.min(y_indices)

        # 蓋の左右の幅を割り出す
        mask_top = (y_indices >= top_y) & (y_indices <= top_y + 40)
        if np.any(mask_top):
            x_in_top = x_indices[mask_top]
            left_x = np.min(x_in_top)
            right_x = np.max(x_in_top)

            lid_height = 35
            width = right_x - left_x

            is_error = False
            error_reason = ""

            if width > 10:
                center_x = (left_x + right_x) // 2
                margin = 8

                # 【重要】左端、中央、右端付近のエッジ座標をそれぞれ取得
                left_mask = (
                    (x_indices >= left_x)
                    & (x_indices <= left_x + margin)
                    & (y_indices >= top_y)
                    & (y_indices <= top_y + lid_height)
                )
                center_mask = (
                    (x_indices >= center_x - margin)
                    & (x_indices <= center_x + margin)
                    & (y_indices >= top_y)
                    & (y_indices <= top_y + lid_height)
                )
                right_mask = (
                    (x_indices >= right_x - margin)
                    & (x_indices <= right_x)
                    & (y_indices >= top_y)
                    & (y_indices <= top_y + lid_height)
                )

                if np.any(left_mask) and np.any(center_mask) and np.any(right_mask):
                    # それぞれのエリアにある最も高い位置（最小のy座標）を取得
                    y_left = np.min(y_indices[left_mask])
                    y_center = np.min(y_indices[center_mask])
                    y_right = np.min(y_indices[right_mask])

                    # --- 厳密な水平・形状チェック ---
                    # 1. 左右の高さの差（左右の傾き）
                    dy_side = abs(y_right - y_left)
                    angle_side = np.degrees(np.arctan2(y_right - y_left, width))

                    # 2. 中央の高さのズレ（山型・谷型・お椀状になっていないか）
                    # 左右の平均高さと、中央の高さの差を計算
                    y_side_avg = (y_left + y_right) / 2.0
                    curve_diff = abs(y_side_avg - y_center)

                    # 判定基準（許容するズレのピクセル数や角度）
                    # ・左右の傾きが 3度超
                    # ・または、左・中・右の高さのバラつき（最大と最小の差）が 5ピクセル以上
                    max_y = max(y_left, y_center, y_right)
                    min_y = min(y_left, y_center, y_right)
                    height_variation = max_y - min_y

                    if abs(angle_side) > 3.0:
                        is_error = True
                        error_reason = f"Side Tilt ({abs(angle_side):.1f}deg)"
                    elif (
                        height_variation > 5.0
                    ):  # 5ピクセル以上高低差があればエラー（山型・歪みを検知）
                        is_error = True
                        error_reason = f"Uneven/Slanted Top"

            # --- 判定結果に応じて枠や文字の色を変更 ---
            box_color = (0, 0, 255) if not is_error else (0, 165, 255)

            pt1 = (left_x - 3, top_y)
            pt2 = (right_x + 3, top_y + lid_height)

            cv2.rectangle(edges_colored, pt1, pt2, box_color, 3)

            if is_error:
                cv2.putText(
                    edges_colored,
                    f"ERROR! {error_reason}",
                    (pt1[0] - 20, top_y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )
            else:
                cv2.putText(
                    edges_colored,
                    "Lid (OK)",
                    (pt1[0], top_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

    # 4. 画面に表示
    cv2.imshow("Webカメラ映像 (厳密な水平・形状判定)", edges_colored)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
