import threading
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk
from cap_inspector import CapInspectorClient


class CapInspectorGUI:
    def __init__(self, root, host="127.0.0.1", port=50051):
        self.root = root
        self.root.title("CapInspector")
        self.client = CapInspectorClient(host, port)
        self.running = True
        self.vars = {}
        self.current_image_size = None
        self.roi_start = None
        self.roi_rect = None

        self.image_canvas = tk.Canvas(root, highlightthickness=1, highlightbackground="gray")
        self.image_canvas.grid(row=0, column=0, rowspan=20, padx=8, pady=8)
        self.image_canvas.bind("<ButtonPress-1>", self._roi_press)
        self.image_canvas.bind("<B1-Motion>", self._roi_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self._roi_release)

        params = self.client.get_parameters()
        row = 0
        for key in ("camera_id", "roi_x_range", "roi_y_range", "angle_limit",
                    "threshold_val", "min_aspect_ratio", "smooth_frames"):
            ttk.Label(root, text=key).grid(row=row, column=1, sticky="w", padx=4, pady=2)
            value = params[key]
            if isinstance(value, (tuple, list)):
                value = ", ".join(str(v) for v in value)
            var = tk.StringVar(value=str(value))
            ttk.Entry(root, textvariable=var, width=24).grid(row=row, column=2, padx=4, pady=2)
            self.vars[key] = var
            row += 1

        ttk.Button(root, text="Apply", command=self.apply_parameters).grid(
            row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=8
        )
        row += 1
        self.status_var = tk.StringVar(value="is_safe: --")
        ttk.Label(root, textvariable=self.status_var).grid(
            row=row, column=1, columnspan=2, sticky="w", padx=4, pady=4
        )

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self._stream_worker, daemon=True).start()

    def _parse_parameters(self):
        def pair(name):
            values = [float(x.strip()) for x in self.vars[name].get().split(",")]
            if len(values) != 2:
                raise ValueError(f"{name} requires two values")
            return tuple(values)
        return {
            "camera_id": int(self.vars["camera_id"].get()),
            "roi_x_range": pair("roi_x_range"),
            "roi_y_range": pair("roi_y_range"),
            "angle_limit": float(self.vars["angle_limit"].get()),
            "threshold_val": int(self.vars["threshold_val"].get()),
            "min_aspect_ratio": float(self.vars["min_aspect_ratio"].get()),
            "smooth_frames": int(self.vars["smooth_frames"].get()),
        }

    def apply_parameters(self):
        try:
            self.client.set_parameters(self._parse_parameters())
        except Exception as exc:
            messagebox.showerror("Parameter error", str(exc))

    def _stream_worker(self):
        try:
            for item in self.client.stream_call("image_stream", 85, 0.1):
                if not self.running:
                    break
                data = np.frombuffer(item["image"], dtype=np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                self.root.after(0, self._update_image, image, item)
        except Exception as exc:
            if self.running:
                self.root.after(0, self.status_var.set, f"stream error: {exc}")

    def _update_image(self, image, item):
        if not self.running:
            return
        photo = ImageTk.PhotoImage(image=image)
        width, height = image.size
        self.current_image_size = (width, height)
        self.image_canvas.configure(width=width, height=height)
        self.image_canvas.delete("frame")
        self.image_canvas.create_image(0, 0, anchor="nw", image=photo, tags="frame")
        self.image_canvas.tag_lower("frame")
        self.image_canvas.image = photo
        reason = item.get("reason")
        self.status_var.set(f"is_safe: {item.get('is_safe')}" + (f" / {reason}" if reason else ""))

    def _roi_press(self, event):
        if self.current_image_size is None:
            return
        self.roi_start = self._clamp_canvas_point(event.x, event.y)
        if self.roi_rect is not None:
            self.image_canvas.delete(self.roi_rect)
        x, y = self.roi_start
        self.roi_rect = self.image_canvas.create_rectangle(x, y, x, y, width=2)

    def _roi_drag(self, event):
        if self.roi_start is None or self.roi_rect is None:
            return
        x, y = self._clamp_canvas_point(event.x, event.y)
        x0, y0 = self.roi_start
        self.image_canvas.coords(self.roi_rect, x0, y0, x, y)

    def _roi_release(self, event):
        if self.roi_start is None or self.current_image_size is None:
            return
        x1, y1 = self._clamp_canvas_point(event.x, event.y)
        x0, y0 = self.roi_start
        self.roi_start = None

        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        width, height = self.current_image_size
        if right - left < 2 or bottom - top < 2:
            return

        roi_x = (left / width, right / width)
        roi_y = (top / height, bottom / height)
        self.vars["roi_x_range"].set(f"{roi_x[0]:.6f}, {roi_x[1]:.6f}")
        self.vars["roi_y_range"].set(f"{roi_y[0]:.6f}, {roi_y[1]:.6f}")
        self.apply_parameters()

    def _clamp_canvas_point(self, x, y):
        width, height = self.current_image_size
        return max(0, min(x, width)), max(0, min(y, height))

    def close(self):
        self.running = False
        self.client.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    CapInspectorGUI(root)
    root.mainloop()
