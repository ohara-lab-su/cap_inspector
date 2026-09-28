# --瓶の下部分を認識し、黄色線で示す--
import cv2
import numpy as np

# カメラの初期化
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape

    # --- 1. ROI（注目領域）の設定 ---
    # キャップが存在する画面上部（0%～35%の範囲）のみ切り出し
    roi_limit_y = int(height * 0.35)
    roi = frame[0:roi_limit_y, 0:width]

    # --- 2. 白色の抽出（グレースケール＋二値化） ---
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 敷居値（200以上を白とみなす）。検出が弱い場合は 180～220 で微調整してください
    _, thresh = cv2.threshold(gray_roi, 200, 255, cv2.THRESH_BINARY)

    # ノイズ除去
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # --- 3. 輪郭検出 ---
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # 面積フィルタリング（小さすぎるノイズを除外）
        if area < 800:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h

        # キャップのアスペクト比（横長：横幅が高さの1.8倍～4.0倍程度）
        if 1.8 <= aspect_ratio <= 4.0:
            # ROI内での最下端Y座標
            bottom_y_roi = y + h

            # 検出枠の描画（緑色）
            cv2.rectangle(frame, (x, y), (x + w, bottom_y_roi), (0, 255, 0), 2)

            # --- 4. 最下ラインの表示（赤色） ---
            cv2.line(
                frame,
                (x, bottom_y_roi),
                (x + w, bottom_y_roi),
                (0, 0, 255),
                3,
            )

    # 検出領域の境界線を表示（参考用：黄色）
    cv2.line(frame, (0, roi_limit_y), (width, roi_limit_y), (0, 255, 255), 1)

    # ウィンドウ表示（文字化けを防ぐため英字タイトル）
    cv2.imshow("Webcam - White Cap Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
