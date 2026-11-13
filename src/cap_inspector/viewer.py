from typing import Any, Callable, Dict, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImageLabel(QLabel):
    """認識済み画像をそのまま表示する。"""

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def set_frame(self, pixmap: QPixmap, width: int, height: int) -> None:
        self.setFixedSize(width, height)
        self.setPixmap(pixmap)


class StreamWorker(QObject):
    frame_ready = Signal(object, object)
    stream_error = Signal(str)
    finished = Signal()

    def __init__(self, inspector: Any, jpeg_quality: int, interval_sec: float) -> None:
        super().__init__()
        self.inspector = inspector
        self.jpeg_quality = jpeg_quality
        self.interval_sec = interval_sec
        self.running = True

    def run(self) -> None:
        try:
            for item in self.inspector.image_stream(
                self.jpeg_quality,
                self.interval_sec,
            ):
                if not self.running:
                    break
                data = np.frombuffer(item["image"], dtype=np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame_ready.emit(frame, item)
        except Exception as exc:
            if self.running:
                self.stream_error.emit(str(exc))
        finally:
            self.finished.emit()

    def stop(self) -> None:
        self.running = False


class CapInspectorViewer(QMainWindow):
    """CapInspector / CapInspectorClient 共通 GUI viewer。"""

    def __init__(
        self,
        inspector: Any,
        close_callback: Optional[Callable[[], None]] = None,
        jpeg_quality: int = 85,
        interval_sec: float = 0.1,
    ) -> None:
        super().__init__()
        self.inspector = inspector
        self.close_callback = close_callback
        self.jpeg_quality = jpeg_quality
        self.interval_sec = interval_sec

        # GUIを実行しているマシン上で読み書きするデフォルトファイル。
        # 呼び出し側から引数として渡さない。
        self.parameter_file = "cap_inspector_parameters.json"

        self.inputs: Dict[str, QLineEdit] = {}
        self._closed = False

        self.setWindowTitle("CapInspector")
        self.image_label = ImageLabel()

        params = self.inspector.get_parameters()
        form_layout = QFormLayout()
        for key in (
            "camera_id",
            "BOTTLE_RIM_Y",
            "MM_TO_PIXEL",
            "TARGET_CLOSE_MM",
            "TARGET_OPEN_MM",
            "TOLERANCE_MM",
            "mode",
        ):
            value = params[key]
            if isinstance(value, (tuple, list)):
                value = ", ".join(str(item) for item in value)
            line_edit = QLineEdit(str(value))
            form_layout.addRow(key, line_edit)
            self.inputs[key] = line_edit

        apply_button = QPushButton("Apply Parameters")
        apply_button.clicked.connect(self.apply_parameters)
        form_layout.addRow(apply_button)

        self.parameter_file_input = QLineEdit(self.parameter_file)
        form_layout.addRow("parameter_file", self.parameter_file_input)

        file_buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_parameters)
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_parameters)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_parameter_file)
        file_buttons.addWidget(save_button)
        file_buttons.addWidget(load_button)
        file_buttons.addWidget(browse_button)
        form_layout.addRow(file_buttons)

        check_buttons = QHBoxLayout()
        open_button = QPushButton("Check OPEN")
        open_button.clicked.connect(self.check_open)
        close_button = QPushButton("Check CLOSE")
        close_button.clicked.connect(self.check_close)
        check_buttons.addWidget(open_button)
        check_buttons.addWidget(close_button)
        form_layout.addRow(check_buttons)

        self.status_label = QLabel("is_safe: --")
        self.status_label.setWordWrap(True)
        form_layout.addRow(self.status_label)

        control_widget = QWidget()
        control_widget.setLayout(form_layout)

        layout = QHBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(control_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.stream_thread = QThread(self)
        self.stream_worker = StreamWorker(
            inspector=self.inspector,
            jpeg_quality=self.jpeg_quality,
            interval_sec=self.interval_sec,
        )
        self.stream_worker.moveToThread(self.stream_thread)
        self.stream_thread.started.connect(self.stream_worker.run)
        self.stream_worker.frame_ready.connect(self._update_image)
        self.stream_worker.stream_error.connect(self._stream_error)
        self.stream_worker.finished.connect(self.stream_thread.quit)
        self.stream_thread.start()

    def _parse_parameters(self) -> Dict[str, Any]:
        return {
            "camera_id": int(self.inputs["camera_id"].text()),
            "BOTTLE_RIM_Y": int(self.inputs["BOTTLE_RIM_Y"].text()),
            "MM_TO_PIXEL": float(self.inputs["MM_TO_PIXEL"].text()),
            "TARGET_CLOSE_MM": float(self.inputs["TARGET_CLOSE_MM"].text()),
            "TARGET_OPEN_MM": float(self.inputs["TARGET_OPEN_MM"].text()),
            "TOLERANCE_MM": float(self.inputs["TOLERANCE_MM"].text()),
            "mode": self.inputs["mode"].text().strip(),
        }

    def apply_parameters(self) -> None:
        try:
            self.inspector.set_parameters(self._parse_parameters())
        except Exception as exc:
            QMessageBox.critical(self, "Parameter error", str(exc))

    def _update_inputs(self, parameters: Dict[str, Any]) -> None:
        for key, value in parameters.items():
            if key not in self.inputs:
                continue
            if isinstance(value, (tuple, list)):
                text = ", ".join(str(item) for item in value)
            else:
                text = str(value)
            self.inputs[key].setText(text)

    def select_parameter_file(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Parameter file",
            self.parameter_file_input.text(),
            "JSON (*.json);;All files (*)",
        )
        if filename:
            self.parameter_file_input.setText(filename)

    def save_parameters(self) -> None:
        try:
            self.inspector.set_parameters(self._parse_parameters())
            filename = self.parameter_file_input.text().strip()
            if not filename:
                raise ValueError("parameter file is empty")
            parameters = self.inspector.save_parameters(filename)
            self._update_inputs(parameters)
            self.status_label.setText("parameters saved: " + filename)
        except Exception as exc:
            QMessageBox.critical(self, "Save error", str(exc))

    def load_parameters(self) -> None:
        try:
            filename = self.parameter_file_input.text().strip()
            if not filename:
                raise ValueError("parameter file is empty")
            parameters = self.inspector.load_parameters(filename)
            self._update_inputs(parameters)
            self.status_label.setText("parameters loaded: " + filename)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))

    def check_open(self) -> None:
        try:
            result = bool(self.inspector.inspect("opened"))
            state = bool(self.inspector.is_open())
            if result != state:
                raise RuntimeError("開栓判定結果と保持状態が一致しません")
            self.status_label.setText("OPEN: " + str(result))
        except Exception as exc:
            QMessageBox.critical(self, "OPEN check error", str(exc))

    def check_close(self) -> None:
        try:
            result = bool(self.inspector.inspect("closed"))
            state = bool(self.inspector.is_closed())
            if result != state:
                raise RuntimeError("閉栓判定結果と保持状態が一致しません")
            self.status_label.setText("CLOSE: " + str(result))
        except Exception as exc:
            QMessageBox.critical(self, "CLOSE check error", str(exc))

    def _update_image(self, frame: np.ndarray, item: Dict[str, Any]) -> None:
        height, width, channels = frame.shape

        bytes_per_line = channels * width
        image = QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        self.image_label.set_frame(QPixmap.fromImage(image), width, height)

        reason = item.get("reason")
        status = "is_safe: " + str(item.get("is_safe"))
        if reason:
            status += " / " + str(reason)
        self.status_label.setText(status)

    def _stream_error(self, message: str) -> None:
        self.status_label.setText("stream error: " + message)

    def closeEvent(self, event: Any) -> None:
        if self._closed:
            event.accept()
            return
        self._closed = True
        self.stream_worker.stop()
        if self.close_callback is not None:
            self.close_callback()
        self.stream_thread.quit()
        self.stream_thread.wait(2000)
        event.accept()


def run_viewer(
    inspector: Any,
    close_callback: Optional[Callable[[], None]] = None,
    jpeg_quality: int = 85,
    interval_sec: float = 0.1,
) -> int:
    """CapInspectorViewer を起動する。"""
    app = QApplication.instance()
    owns_application = False
    if app is None:
        app = QApplication([])
        owns_application = True

    viewer = CapInspectorViewer(
        inspector=inspector,
        close_callback=close_callback,
        jpeg_quality=jpeg_quality,
        interval_sec=interval_sec,
    )
    viewer.show()

    if owns_application:
        return app.exec()
    return 0


if __name__ == "__main__":
    from cap_inspector import CapInspector
    from x_logger import XLogger

    CAMERA_ID = 0
    logger = XLogger(logger_name="cap_inspector_local_viewer")
    inspector = CapInspector(camera_id=CAMERA_ID, logger=logger)
    run_viewer(
        inspector=inspector,
        close_callback=inspector.release,
    )
