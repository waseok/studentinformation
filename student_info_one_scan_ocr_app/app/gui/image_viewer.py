"""스캔 이미지 미리보기(확대·회전)."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = self._scene.addPixmap(QPixmap())
        self._rotation = 0
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def load_path(self, path: str | Path) -> None:
        p = Path(path)
        if not p.is_file():
            return
        img = QImage(str(p))
        self._pixmap_item.setPixmap(QPixmap.fromImage(img))
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def rotate_90(self) -> None:
        self._rotation = (self._rotation + 90) % 360
        self.setTransform(QTransform().rotate(self._rotation))

    def reset_view(self) -> None:
        self._rotation = 0
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
