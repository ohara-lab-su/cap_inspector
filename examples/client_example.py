from cap_inspector import CapInspectorClient
import sys

### 最初に一回だけ実行して client インスタンスを生成する
camera = CapInspectorClient("10.170.55", 50051)
# print(client.get_parameters())
camera.start_camera()
camera.inspect()

############
### ロボット処理
############

# print(camera.is_safe())
# print(camera.get_status())
if not camera.inspect():
    sys.exit()
    # False

############
### ロボット処理
############

# ロボット操作を終えたあと
camera.stop_camera()

# camera.close()
