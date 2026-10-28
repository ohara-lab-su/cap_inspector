# 赤い蓋での認識
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
            # 輪郭を囲む外接矩形を取得 (x, y: 左上の座標, w: 幅, h: 高さ)
            x, y, w, h = cv2.boundingRect(cnt)

            # 4. 全体を緑色の枠線で囲む (B, G, R) -> 緑: (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 5. 蓋の底部分（矩形の下辺）に黄色い線を引く (B, G, R) -> 黄色: (0, 255, 255)
            # 始点: (x, y + h), 終点: (x + w, y + h)
            cv2.line(frame, (x, y + h), (x + w, y + h), (0, 255, 255), 3)

            # テキスト表示
            cv2.putText(
                frame,
                "Red Cap",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

    # 映像を表示
    cv2.imshow("Webカメラ映像", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
