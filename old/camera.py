# ---カメラにうつる画像の表示--
import cv2

# カメラを初期化
cap = cv2.VideoCapture(1)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Webカメラ映像", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
