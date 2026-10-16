from typing import Any, Callable, Dict, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QObject, QPoint, QRect, Qt, QThread, Signal
from PySide6.QtGui import QImage, QMouseEvent, QPainter, QPen, QPixmap
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
        parameter_file: str = "cap_inspector_parameters.json",
    ) -> None:
        super().__init__()
        self.inspector = inspector
        self.close_callback = close_callback
        self.jpeg_quality = jpeg_quality
        self.interval_sec = interval_sec
        self.parameter_file = parameter_file
        self.inputs: Dict[str, QLineEdit] = {}
        self._closed = False
        self.reference_cap: Optional[Dict[str, Any]] = None

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
            "cap_actual_width_mm",
            "position_limit_mm",
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

        calibrate_button = QPushButton("Calibrate Closed CAP")
        calibrate_button.clicked.connect(self.calibrate)
        form_layout.addRow(calibrate_button)

        check_buttons = QHBoxLayout()
        open_button = QPushButton("Check OPEN")
        open_button.clicked.connect(self.check_open)
        close_button = QPushButton("Check CLOSE")
        close_button.clicked.connect(self.check_close)
        check_buttons.addWidget(open_button)
        check_buttons.addWidget(close_button)
        form_layout.addRow(check_buttons)

        self.calibration_label = QLabel("calibration: --")
        self.calibration_label.setWordWrap(True)
        form_layout.addRow(self.calibration_label)

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
            "cap_actual_width_mm": float(
                self.inputs["cap_actual_width_mm"].text()
            ),
            "position_limit_mm": float(
                self.inputs["position_limit_mm"].text()
            ),
        }

    def apply_parameters(self) -> bool:
        try:
            parameters = self.inspector.set_parameters(self._parse_parameters())
            self._update_inputs(parameters)
            self.status_label.setText("parameters applied")
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Parameter error", str(exc))
            return False

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
            if not self.apply_parameters():
                return
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
            self.reference_cap = self.inspector.get_reference_cap()
            self.calibration_label.setText(
                "calibration: parameters loaded / confirm or recalibrate"
            )
            self.status_label.setText("parameters loaded: " + filename)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))

    def calibrate(self) -> None:
        try:
            if not self.apply_parameters():
                return
            result = bool(self.inspector.calibrate())
            self.reference_cap = self.inspector.get_reference_cap()
            if result:
                filename = self.parameter_file_input.text().strip()
                if filename:
                    self.inspector.save_parameters(filename)
                self.calibration_label.setText(
                    "calibration: OK / reference_cap="
                    + str(self.reference_cap)
                )
            else:
                self.calibration_label.setText("calibration: FAIL")
        except Exception as exc:
            QMessageBox.critical(self, "Calibration error", str(exc))

    def check_open(self) -> None:
        try:
            # Stream表示もOPEN判定に合わせる。
            self.inspector.set_parameters({"mode": "open"})
            result = bool(self.inspector.is_open())
            status = self.inspector.get_status()
            self.reference_cap = self.inspector.get_reference_cap()
            self.status_label.setText(
                "OPEN: "
                + str(result)
                + " / "
                + str(status.get("reason"))
            )
        except Exception as exc:
            QMessageBox.critical(self, "OPEN check error", str(exc))

    def check_close(self) -> None:
        try:
            # Stream表示もCLOSE判定に合わせる。
            self.inspector.set_parameters({"mode": "closed"})
            result = bool(self.inspector.is_closed())
            status = self.inspector.get_status()
            self.reference_cap = self.inspector.get_reference_cap()
            self.status_label.setText(
                "CLOSE: "
                + str(result)
                + " / "
                + str(status.get("reason"))
            )
        except Exception as exc:
            QMessageBox.critical(self, "CLOSE check error", str(exc))

    def _update_image(self, frame: np.ndarray, item: Dict[str, Any]) -> None:
        height, width, channels = frame.shape

        try:
            roi_x = [
                float(value.strip())
                for value in self.inputs["roi_x_range"].text().split(",")
            ]
            roi_y = [
                float(value.strip())
                for value in self.inputs["roi_y_range"].text().split(",")
            ]
            if len(roi_x) == 2 and len(roi_y) == 2:
                x1 = int(roi_x[0] * width)
                x2 = int(roi_x[1] * width)
                y1 = int(roi_y[0] * height)
                y2 = int(roi_y[1] * height)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        except (TypeError, ValueError):
            pass

        if self.reference_cap is not None:
            ref_x = int(self.reference_cap["x"])
            ref_top = int(self.reference_cap["top_y"])
            ref_width = int(self.reference_cap["width"])
            ref_bottom = int(self.reference_cap["bottom_y"])
            cv2.rectangle(
                frame,
                (ref_x, ref_top),
                (ref_x + ref_width, ref_bottom),
                (255, 255, 0),
                2,
            )
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
        if self.apply_parameters():
            self.reference_cap = None
            self.calibration_label.setText(
                "calibration: ROI changed / recalibration required"
            )

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
    parameter_file: str = "cap_inspector_parameters.json",
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
        parameter_file=parameter_file,
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
