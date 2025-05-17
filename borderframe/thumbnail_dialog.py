from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QScrollArea,
    QWidget,
    QGridLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap

from .utils import load_pixmap
import os


class ThumbnailDialog(QDialog):
    """Dialog that displays thumbnails of images with delete options."""

    def __init__(self, parent=None, images=None):
        super().__init__(parent)
        self.parent = parent
        self.images = images or []
        self.setWindowTitle("Thumbnail View")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.thumbnail_cache = {}
        self.thumbnail_size = QSize(180, 180)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        close_button = QPushButton("Close")
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            """
        )
        close_button.clicked.connect(self.close)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        QTimer.singleShot(0, self.update_thumbnails)

    def create_thumbnail(self, image_path):
        if image_path in self.thumbnail_cache:
            return self.thumbnail_cache[image_path]

        pixmap = load_pixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_cache[image_path] = scaled_pixmap
            return scaled_pixmap
        return None

    def create_thumbnail_frame(self, image_path, idx):
        frame = QFrame()
        frame.setFixedSize(250, 280)
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet(
            """
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            """
        )

        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(8)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        image_container = QWidget()
        image_container.setFixedSize(self.thumbnail_size)
        image_container.setStyleSheet("background-color: #f8f9fa;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        scaled_pixmap = self.create_thumbnail(image_path)
        if scaled_pixmap:
            thumb_label = QLabel()
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setPixmap(scaled_pixmap)
            image_layout.addWidget(thumb_label, 0, Qt.AlignCenter)

        frame_layout.addWidget(image_container, 0, Qt.AlignCenter)

        filename = os.path.basename(image_path)
        if len(filename) > 20:
            filename = filename[:17] + "..."
        name_label = QLabel(filename)
        name_label.setFixedHeight(20)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(
            """
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            """
        )
        frame_layout.addWidget(name_label)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(100, 30)
        delete_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            """
        )
        delete_btn.clicked.connect(lambda checked, x=idx: self.delete_image(x))
        frame_layout.addWidget(delete_btn, 0, Qt.AlignCenter)

        return frame

    def update_thumbnails(self):
        self.container.setUpdatesEnabled(False)

        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        columns = 4
        batch_size = 12

        def load_batch(start_idx):
            if start_idx >= len(self.images):
                self.container.setUpdatesEnabled(True)
                return

            end_idx = min(start_idx + batch_size, len(self.images))

            for idx in range(start_idx, end_idx):
                image_path = self.images[idx]
                frame = self.create_thumbnail_frame(image_path, idx)
                row = idx // columns
                col = idx % columns
                self.grid_layout.addWidget(frame, row, col)

            QTimer.singleShot(10, lambda: load_batch(end_idx))

        load_batch(0)

    def delete_image(self, index):
        if 0 <= index < len(self.images):
            self.container.setUpdatesEnabled(False)

            image_path = self.images[index]
            was_current = index == self.parent.current_preview_index

            if image_path in self.thumbnail_cache:
                del self.thumbnail_cache[image_path]

            del self.images[index]
            self.parent.selected_images = self.images

            if len(self.images) == 0:
                self.parent.current_preview_index = -1
                self.parent.current_pixmap = None
            elif was_current:
                self.parent.current_preview_index = min(index, len(self.images) - 1)
            elif index < self.parent.current_preview_index:
                self.parent.current_preview_index -= 1

            if was_current:
                self.parent.force_preview_update()
            else:
                self.parent.update_preview()

            self.update_thumbnails()

