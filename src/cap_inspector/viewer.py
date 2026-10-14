from typing import Any, Callable, Dict, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QObject, QPoint, QRect, Qt, QThread, Signal
from PySide6.QtGui import QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
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
    roi_selected = Signal(float, float, float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setMouseTracking(True)
        self._image_size: Optional[Tuple[int, int]] = None
        self._roi_start: Optional[QPoint] = None
        self._roi_end: Optional[QPoint] = None

    def set_frame(self, pixmap: QPixmap, width: int, height: int) -> None:
        self._image_size = (width, height)
        self.setFixedSize(width, height)
        self.setPixmap(pixmap)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._image_size is None:
            return
        point = self._clamp_point(event.position().toPoint())
        self._roi_start = point
        self._roi_end = point
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._roi_start is None:
            return
        self._roi_end = self._clamp_point(event.position().toPoint())
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._roi_start is None or self._image_size is None:
            return

        self._roi_end = self._clamp_point(event.position().toPoint())
        start = self._roi_start
        end = self._roi_end
        self._roi_start = None
        self._roi_end = None
        self.update()

        left = min(start.x(), end.x())
        right = max(start.x(), end.x())
        top = min(start.y(), end.y())
        bottom = max(start.y(), end.y())
        if right - left < 2 or bottom - top < 2:
            return

        width, height = self._image_size
        self.roi_selected.emit(
            left / float(width),
            right / float(width),
            top / float(height),
            bottom / float(height),
        )

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        if self._roi_start is None or self._roi_end is None:
            return
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.drawRect(QRect(self._roi_start, self._roi_end).normalized())
        painter.end()

    def _clamp_point(self, point: QPoint) -> QPoint:
        if self._image_size is None:
            return QPoint(0, 0)
        width, height = self._image_size
        x = max(0, min(point.x(), width))
        y = max(0, min(point.y(), height))
        return QPoint(x, y)


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
        self.inputs: Dict[str, QLineEdit] = {}
        self._closed = False

        self.setWindowTitle("CapInspector")
        self.image_label = ImageLabel()
        self.image_label.roi_selected.connect(self._roi_selected)

        params = self.inspector.get_parameters()
        form_layout = QFormLayout()
        for key in (
            "camera_id",
            "roi_x_range",
            "roi_y_range",
            "angle_limit",
            "threshold_val",
            "min_aspect_ratio",
            "smooth_frames",
        ):
            value = params[key]
            if isinstance(value, (tuple, list)):
                value = ", ".join(str(item) for item in value)
            line_edit = QLineEdit(str(value))
            form_layout.addRow(key, line_edit)
            self.inputs[key] = line_edit

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_parameters)
        form_layout.addRow(apply_button)

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
        def pair(name: str) -> Tuple[float, float]:
            values = [
                float(value.strip()) for value in self.inputs[name].text().split(",")
            ]
            if len(values) != 2:
                raise ValueError(name + " requires two values")
            return values[0], values[1]

        return {
            "camera_id": int(self.inputs["camera_id"].text()),
            "roi_x_range": pair("roi_x_range"),
            "roi_y_range": pair("roi_y_range"),
            "angle_limit": float(self.inputs["angle_limit"].text()),
            "threshold_val": int(self.inputs["threshold_val"].text()),
            "min_aspect_ratio": float(self.inputs["min_aspect_ratio"].text()),
            "smooth_frames": int(self.inputs["smooth_frames"].text()),
        }

    def apply_parameters(self) -> None:
        try:
            self.inspector.set_parameters(self._parse_parameters())
        except Exception as exc:
            QMessageBox.critical(self, "Parameter error", str(exc))

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

    def _roi_selected(
        self,
        left: float,
        right: float,
        top: float,
        bottom: float,
    ) -> None:
        self.inputs["roi_x_range"].setText("{:.6f}, {:.6f}".format(left, right))
        self.inputs["roi_y_range"].setText("{:.6f}, {:.6f}".format(top, bottom))
        self.apply_parameters()

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
