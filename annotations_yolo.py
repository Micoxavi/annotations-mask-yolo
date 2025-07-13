"""
segmentation_mask_yolo.py

PEP 8-compliant multiregion segmentation tool with YOLO export.

Run with:
    python segmentation_mask_yolo.py
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

import cv2
import numpy as np
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Point = Tuple[int, int]


class ZoomableGraphicsView(QGraphicsView):
    """
    Graphics view that supports scroll-wheel zoom & double-click closure.
    """

    def __init__(self, scene: QGraphicsScene, parent_app: "SegmentationApp") -> None:
        super().__init__(scene)
        self._app = parent_app

        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    # ---------------------------------------------------------------------
    # Event handlers
    # ---------------------------------------------------------------------
    def mouseDoubleClickEvent(self, event):  
        """
        Close the current polygon on left double-click.
        """
        if event.button() == Qt.LeftButton:
            self._app.close_polygon()
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):  
        """
        Zoom in/out keeping the cursor position fixed.
        """
        factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        self.scale(factor, factor)

    def mousePressEvent(self, event):  
        """
        Add a vertex on left click.
        """
        if event.button() == Qt.LeftButton and self._app.image is not None:
            pos = self.mapToScene(event.pos())
            self._app.add_point((int(pos.x()), int(pos.y())))
        super().mousePressEvent(event)


class SegmentationApp(QMainWindow):
    """
    GUI application for drawing regions and exporting annotations.
    """

    # ------------------------------------------------------------------
    # Construction & layout
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Segmentación multirregión (máscara + YOLO)")

        # Runtime state --------------------------------------------------
        self.current_points: List[Point] = []
        self.preview_item = None  # QGraphicsPathItem preview
        self.annotations: List[Tuple[List[Point], int]] = []
        self.image: np.ndarray | None = None
        self.image_path: str = ""
        self.pixmap_item = None  # QGraphicsPixmapItem

        # Scene & view ---------------------------------------------------
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene, self)

        # Controls -------------------------------------------------------
        self.load_btn = QPushButton("Cargar imagen")
        self.save_mask_btn = QPushButton("Guardar máscara")
        self.save_yolo_btn = QPushButton("Guardar YOLO")
        self.undo_btn = QPushButton("Deshacer polígono")
        self.reset_btn = QPushButton("Borrar todo")

        self.class_label = QLabel("Clase activa:")
        self.class_spin = QSpinBox()
        self.class_spin.setRange(0, 9999)

        self._connect_signals()
        self._build_layout()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        """
        Connect Qt signals to slots.
        """
        self.load_btn.clicked.connect(self.load_image)
        self.save_mask_btn.clicked.connect(self.save_mask)
        self.save_yolo_btn.clicked.connect(self.save_yolo)
        self.undo_btn.clicked.connect(self.clear_polygon)
        self.reset_btn.clicked.connect(self.delete_image)

    def _build_layout(self) -> None:
        """
        Arrange widgets in the main window.
        """
        controls = QHBoxLayout()
        for widget in (
            self.load_btn,
            self.save_mask_btn,
            self.save_yolo_btn,
            self.undo_btn,
            self.reset_btn,
            self.class_label,
            self.class_spin,
        ):
            controls.addWidget(widget)

        main_lay = QVBoxLayout()
        main_lay.addLayout(controls)
        main_lay.addWidget(self.view)

        container = QWidget()
        container.setLayout(main_lay)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------
    # Image loading / reset
    # ------------------------------------------------------------------
    def load_image(self) -> None:
        """
        Open an image file and display it inside the scene.
        """
        self.delete_image()

        path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona imagen", "../datasets"
        )
        if not path:
            return

        img_bgr = cv2.imread(path)
        if img_bgr is None:
            QMessageBox.warning(self, "Error", "No se pudo leer la imagen.")
            return

        self.image_path = path
        self.image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        height, width, _ = self.image.shape
        qimg = QImage(
            self.image.data,
            width,
            height,
            3 * width,
            QImage.Format_RGB888,
        )
        self.pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(qimg))
        self.scene.addItem(self.pixmap_item)
        self.view.resetTransform()

    def delete_image(self) -> None:
        """
        Remove current image and annotations from the scene.
        """
        self.scene.clear()
        self.annotations.clear()
        self.current_points.clear()
        self.preview_item = None
        self.image = None
        self.image_path = ""
        self.pixmap_item = None

    # ------------------------------------------------------------------
    # Polygon drawing
    # ------------------------------------------------------------------
    def add_point(self, point: Point) -> None:
        """
        Append a vertex and update the dashed preview path.
        """
        self.current_points.append(point)

        # Remove previous preview
        if self.preview_item is not None:
            self.scene.removeItem(self.preview_item)

        # Draw the updated open path
        path = QPainterPath(QPointF(*self.current_points[0]))
        for x, y in self.current_points[1:]:
            path.lineTo(QPointF(x, y))
        self.preview_item = self.scene.addPath(
            path,
            QPen(Qt.blue, 1, Qt.DashLine),
        )

    def close_polygon(self) -> None:
        """
        Close and commit the current polygon to *annotations*.
        """
        if len(self.current_points) < 3:
            return

        # Draw permanent polygon
        path = QPainterPath(QPointF(*self.current_points[0]))
        for x, y in self.current_points[1:]:
            path.lineTo(QPointF(x, y))
        path.closeSubpath()
        self.scene.addPath(path, QPen(Qt.red, 2))

        class_id = self.class_spin.value()
        self.annotations.append((self.current_points.copy(), class_id))

        # Reset state
        self.current_points.clear()
        if self.preview_item is not None:
            self.scene.removeItem(self.preview_item)
            self.preview_item = None

    def clear_polygon(self) -> None:
        """
        Undo the last committed polygon or the live preview.
        """
        if self.annotations:
            self.annotations.pop()
            # Remove the most recent red path (first non‑pixmap item)
            for item in self.scene.items():
                if not isinstance(item, QGraphicsPixmapItem):
                    pen = item.pen() if hasattr(item, "pen") else None
                    if pen and pen.color() == Qt.red:
                        self.scene.removeItem(item)
                        break
        elif self.preview_item is not None:
            self.scene.removeItem(self.preview_item)
            self.preview_item = None
            self.current_points.clear()

    # ------------------------------------------------------------------
    # Mask / YOLO export
    # ------------------------------------------------------------------
    def save_mask(self) -> None:
        """
        Fill all polygons into a single-channel mask and save as PNG.
        """
        if self.image is None or not self.annotations:
            return

        height, width = self.image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        for points, _ in self.annotations:
            cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 1)

        base = os.path.splitext(os.path.basename(self.image_path))[0]
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar máscara",
            f"../datasets/{base}_mask.png",
        )
        if save_path:
            cv2.imwrite(save_path, mask * 255)

    @staticmethod
    def _poly_to_bbox_norm(
        points: List[Point], img_w: int, img_h: int
    ) -> Tuple[float, float, float, float]:
        """
        Convert a polygon to a YOLO-style normalised bounding box.
        """
        xs, ys = zip(*points)
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        cx = (x_min + x_max) / 2.0 / img_w
        cy = (y_min + y_max) / 2.0 / img_h
        bw = (x_max - x_min) / img_w
        bh = (y_max - y_min) / img_h
        
        return cx, cy, bw, bh

    def save_yolo(self):
        """
        Save the polygon as a YOLO-style annotation in a txt file.
        """
        if self.image is None or not self.annotations:
            return
        
        h, w = self.image.shape[:2]
        lines = []

        for pts, class_id in self.annotations:
            cx, cy, bw, bh = self._poly_to_bbox_norm(pts, w, h)
            lines.append(f"{class_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

        base = os.path.splitext(os.path.basename(self.image_path))[0]
        save_path, _ = QFileDialog.getSaveFileName(self, "Guardar etiqueta YOLO", f"../datasets/{base}.txt", "Texto (*.txt)")

        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SegmentationApp(); win.show()
    sys.exit(app.exec_())
