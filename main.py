import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                           QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox,
                           QSlider, QColorDialog, QScrollArea, QGridLayout, QLineEdit,
                           QFrame, QSizePolicy, QCheckBox, QProgressDialog,
                           QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QIntValidator, QFont
import os
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import concurrent.futures
from io import BytesIO
import numpy as np

class ThumbnailDialog(QDialog):
    def __init__(self, parent=None, images=None):
        super().__init__(parent)
        self.parent = parent
        self.images = images or []
        self.setWindowTitle("Thumbnail View")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.thumbnail_cache = {}  # Cache for scaled thumbnails
        self.thumbnail_size = QSize(180, 180)  # Fixed thumbnail size
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Scroll area for thumbnails
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)  # Consistent spacing between items
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add thumbnails
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        # Add close button at the bottom
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
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
        """)
        close_button.clicked.connect(self.close)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Start loading thumbnails
        QTimer.singleShot(0, self.update_thumbnails)

    def create_thumbnail(self, image_path):
        if image_path in self.thumbnail_cache:
            return self.thumbnail_cache[image_path]
            
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_cache[image_path] = scaled_pixmap
            return scaled_pixmap
        return None

    def create_thumbnail_frame(self, image_path, idx):
        frame = QFrame()
        frame.setFixedSize(250, 280)  # Fixed size for the entire frame
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(8)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create image container with fixed size
        image_container = QWidget()
        image_container.setFixedSize(self.thumbnail_size)
        image_container.setStyleSheet("background-color: #f8f9fa;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create and add thumbnail
        scaled_pixmap = self.create_thumbnail(image_path)
        if scaled_pixmap:
            thumb_label = QLabel()
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setPixmap(scaled_pixmap)
            image_layout.addWidget(thumb_label, 0, Qt.AlignCenter)
            
        frame_layout.addWidget(image_container, 0, Qt.AlignCenter)
            
        # Add filename label with fixed height
        filename = os.path.basename(image_path)
        if len(filename) > 20:
            filename = filename[:17] + "..."
        name_label = QLabel(filename)
        name_label.setFixedHeight(20)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        frame_layout.addWidget(name_label)
        
        # Add delete button with fixed size
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(100, 30)
        delete_btn.setStyleSheet("""
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
        """)
        delete_btn.clicked.connect(lambda checked, x=idx: self.delete_image(x))
        frame_layout.addWidget(delete_btn, 0, Qt.AlignCenter)
        
        return frame

    def update_thumbnails(self):
        # Block signals during update
        self.container.setUpdatesEnabled(False)
        
        # Clear existing thumbnails
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        # Add thumbnails to grid
        columns = 4
        batch_size = 12  # Number of thumbnails to load at once
        
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
            
            # Schedule next batch
            QTimer.singleShot(10, lambda: load_batch(end_idx))
        
        # Start loading the first batch
        load_batch(0)

    def delete_image(self, index):
        if 0 <= index < len(self.images):
            # Block signals during update
            self.container.setUpdatesEnabled(False)
            
            image_path = self.images[index]
            was_current = index == self.parent.current_preview_index
            
            # Remove from cache
            if image_path in self.thumbnail_cache:
                del self.thumbnail_cache[image_path]
            
            # Update image lists
            del self.images[index]
            self.parent.selected_images = self.images
            
            # Update current preview index and refresh preview
            if len(self.images) == 0:
                self.parent.current_preview_index = -1
                self.parent.current_pixmap = None
            elif was_current:
                self.parent.current_preview_index = min(index, len(self.images) - 1)
            elif index < self.parent.current_preview_index:
                self.parent.current_preview_index -= 1
            
            # Update the UI
            if was_current:
                self.parent.force_preview_update()
            else:
                self.parent.update_preview()
            
            # Update thumbnails
            self.update_thumbnails()

class ImageProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Border Processor")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: white;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: none;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        # Store selected images and current preview
        self.selected_images = []
        self.current_preview_index = 0
        self.current_pixmap = None
        self.preview_size = QSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Left panel for controls
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.StyledPanel)
        left_panel.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_panel.setFixedWidth(320)
        
        # Image Management Section
        img_section = self.create_section("Image Management")
        
        # Add images button
        self.add_button = QPushButton("Add Images")
        self.add_button.setIcon(self.style().standardIcon(self.style().SP_FileDialogStart))
        self.add_button.setToolTip("Select multiple images to process")
        img_section.addWidget(self.add_button)
        
        # Add thumbnail view button
        self.thumbnail_button = QPushButton("Thumbnail View")
        self.thumbnail_button.setIcon(self.style().standardIcon(self.style().SP_FileDialogContentsView))
        self.thumbnail_button.setToolTip("Show thumbnails of all imported images")
        self.thumbnail_button.clicked.connect(self.show_thumbnails)
        img_section.addWidget(self.thumbnail_button)
        
        # Add folder button
        self.folder_button = QPushButton("Add Folder")
        self.folder_button.setIcon(self.style().standardIcon(self.style().SP_DirIcon))
        self.folder_button.setToolTip("Select a folder containing images")
        img_section.addWidget(self.folder_button)
        
        left_layout.addLayout(img_section)
        
        # Border Settings Section
        border_section = self.create_section("Border Settings")
        
        # Aspect ratio selector
        aspect_label = QLabel("Aspect Ratio:")
        aspect_label.setFont(QFont("", weight=QFont.Bold))
        border_section.addWidget(aspect_label)
        
        self.aspect_combo = QComboBox()
        self.aspect_ratios = {
            "Original": None,
            "1:1 (Square)": (1, 1),
            "4:5 (Instagram Portrait)": (4, 5),
            "5:4 (Instagram Landscape)": (5, 4),
            "9:16 (Story)": (9, 16),
            "2:1 (Banner)": (2, 1)
        }
        self.aspect_combo.addItems(self.aspect_ratios.keys())
        self.aspect_combo.setToolTip("Select the desired aspect ratio for the final image")
        border_section.addWidget(self.aspect_combo)
        
        # Border size controls
        size_label = QLabel("Border Size:")
        size_label.setFont(QFont("", weight=QFont.Bold))
        border_section.addWidget(size_label)
        
        slider_layout = QHBoxLayout()
        self.border_slider = QSlider(Qt.Horizontal)
        self.border_slider.setRange(0, 300)
        self.border_slider.setToolTip("Adjust border size")
        
        self.border_size_input = QLineEdit()
        self.border_size_input.setMaximumWidth(60)
        self.border_size_input.setText("0")
        self.border_size_input.setAlignment(Qt.AlignRight)
        self.border_size_input.setValidator(QIntValidator(0, 300))
        
        slider_layout.addWidget(self.border_slider)
        slider_layout.addWidget(self.border_size_input)
        slider_layout.addWidget(QLabel("px"))
        border_section.addLayout(slider_layout)
        
        # Color picker
        color_label = QLabel("Border Color:")
        color_label.setFont(QFont("", weight=QFont.Bold))
        border_section.addWidget(color_label)
        
        self.color_button = QPushButton("Select Color")
        self.color_button.setToolTip("Choose the border color")
        self.border_color = "#FFFFFF"
        self.update_color_button()
        border_section.addWidget(self.color_button)
        
        left_layout.addLayout(border_section)
        
        # Output Settings Section
        output_section = self.create_section("Output Settings")
        
        # Save format selection
        format_label = QLabel("Save Format:")
        format_label.setFont(QFont("", weight=QFont.Bold))
        output_section.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.save_formats = {
            "JPEG (80% quality)": ("JPEG", 80),
            "JPEG (95% quality)": ("JPEG", 95),
            "JPEG (100% quality)": ("JPEG", 100),
            "TIFF": ("TIFF", None),
            "PNG": ("PNG", None),
            "HEIF (80% quality)": ("HEIF", 80),
            "HEIF (95% quality)": ("HEIF", 95),
            "HEIF (100% quality)": ("HEIF", 100)
        }
        self.format_combo.addItems(self.save_formats.keys())
        self.format_combo.setToolTip("Select the output image format and quality")
        output_section.addWidget(self.format_combo)
        
        # Metadata control
        self.preserve_metadata = QCheckBox("Preserve Location Metadata")
        self.preserve_metadata.setToolTip("Keep GPS and location information in processed images")
        self.preserve_metadata.setChecked(True)  # Default to preserving metadata
        output_section.addWidget(self.preserve_metadata)
        
        name_label = QLabel("Save Name (optional):")
        name_label.setFont(QFont("", weight=QFont.Bold))
        output_section.addWidget(name_label)
        
        self.save_name = QLineEdit()
        self.save_name.setPlaceholderText("Enter file name prefix")
        self.save_name.setToolTip("Add a prefix to processed image filenames")
        output_section.addWidget(self.save_name)
        
        # Process button
        self.process_button = QPushButton("Process Images")
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        self.process_button.setToolTip("Start processing all images")
        output_section.addWidget(self.process_button)
        
        left_layout.addLayout(output_section)
        
        # Navigation Section
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.prev_button.setToolTip("View previous image")
        self.next_button.setToolTip("View next image")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        left_layout.addLayout(nav_layout)
        
        left_layout.addStretch()
        
        # Right panel for preview
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.StyledPanel)
        right_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        preview_label = QLabel("Preview")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setFont(QFont("", weight=QFont.Bold))
        right_layout.addWidget(preview_label)
        
        # Preview label in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        right_layout.addWidget(scroll_area)
        
        # Add panels to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, stretch=1)
        
        # Connect signals
        self.add_button.clicked.connect(self.add_images)
        self.folder_button.clicked.connect(self.add_folder)
        self.color_button.clicked.connect(self.select_color)
        self.border_slider.valueChanged.connect(self.update_preview)
        self.border_slider.valueChanged.connect(self.update_border_size_input)
        self.border_size_input.textChanged.connect(self.on_border_size_input)
        self.aspect_combo.currentIndexChanged.connect(self.update_preview)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.process_button.clicked.connect(self.process_images)
        
        # Update initial state
        self.update_navigation_buttons()

    def create_section(self, title):
        section = QVBoxLayout()
        label = QLabel(title)
        label.setFont(QFont("", weight=QFont.Bold))
        section.addWidget(label)
        return section

    def update_color_button(self):
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.border_color};
                border: 2px solid #bdc3c7;
                min-width: 100px;
            }}
            QPushButton:hover {{
                border: 2px solid #95a5a6;
            }}
        """)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if files:
            self.selected_images.extend(files)
            self.current_preview_index = len(self.selected_images) - 1
            self.load_current_image()
            self.update_navigation_buttons()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        self.selected_images.append(os.path.join(root, file))
            if self.selected_images:
                self.current_preview_index = len(self.selected_images) - 1
                self.load_current_image()
                self.update_navigation_buttons()

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.border_color = color.name()
            self.update_color_button()
            self.update_preview()

    def calculate_dimensions(self, img_width, img_height, border_size, aspect_ratio):
        if aspect_ratio is None:
            new_width = img_width + (border_size * 2)
            new_height = img_height + (border_size * 2)
        else:
            target_ratio = aspect_ratio[0] / aspect_ratio[1]
            min_width = img_width + (border_size * 2)
            min_height = img_height + (border_size * 2)
            current_ratio = min_width / min_height
            
            if current_ratio > target_ratio:
                new_width = min_width
                new_height = int(new_width / target_ratio)
                new_height = max(new_height, min_height)
            else:
                new_height = min_height
                new_width = int(new_height * target_ratio)
                new_width = max(new_width, min_width)
        
        return new_width, new_height

    def load_current_image(self):
        if 0 <= self.current_preview_index < len(self.selected_images):
            try:
                self.current_pixmap = QPixmap(self.selected_images[self.current_preview_index])
                self.update_preview()
            except Exception as e:
                print(f"Error loading image: {e}")
                self.current_pixmap = None

    def update_preview(self):
        if not self.current_pixmap:
            return
            
        try:
            # Get current settings
            aspect_ratio = self.aspect_ratios[self.aspect_combo.currentText()]
            border_size = self.border_slider.value()
            
            # Calculate new dimensions based on original image size
            orig_width = self.current_pixmap.width()
            orig_height = self.current_pixmap.height()
            new_width, new_height = self.calculate_dimensions(orig_width, orig_height, border_size, aspect_ratio)
            
            # Create new pixmap with border
            result = QPixmap(new_width, new_height)
            result.fill(QColor(self.border_color))
            
            # Draw original image in center
            painter = QPainter(result)
            paste_x = (new_width - orig_width) // 2
            paste_y = (new_height - orig_height) // 2
            painter.drawPixmap(paste_x, paste_y, self.current_pixmap)
            painter.end()
            
            # Scale for preview
            scaled = result.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            
        except Exception as e:
            print(f"Error updating preview: {e}")

    def force_preview_update(self):
        """Force update the preview with the current index"""
        if not self.selected_images:
            self.preview_label.clear()
            self.preview_label.setText("No images selected")
            self.update_navigation_buttons()
            return
            
        if 0 <= self.current_preview_index < len(self.selected_images):
            image_path = self.selected_images[self.current_preview_index]
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.current_pixmap = pixmap
                self.update_preview()
        else:
            self.preview_label.clear()
            self.preview_label.setText("No image to preview")
        
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_preview_index > 0)
        self.next_button.setEnabled(self.current_preview_index < len(self.selected_images) - 1)

    def prev_image(self):
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            self.load_current_image()
            self.update_navigation_buttons()

    def next_image(self):
        if self.current_preview_index < len(self.selected_images) - 1:
            self.current_preview_index += 1
            self.load_current_image()
            self.update_navigation_buttons()

    def process_images(self):
        if not self.selected_images:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return

        total_images = len(self.selected_images)
        
        # Create progress dialog
        progress = QProgressDialog("Processing images...", "Cancel", 0, total_images, self)
        progress.setWindowTitle("Processing Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 20px;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                padding: 1px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # Prepare settings dictionary
        settings = {
            'base_filename': self.save_name.text().strip(),
            'aspect_ratio': self.aspect_ratios[self.aspect_combo.currentText()],
            'border_size': self.border_slider.value(),
            'save_format': self.save_formats[self.format_combo.currentText()][0],
            'quality': self.save_formats[self.format_combo.currentText()][1],
            'preserve_metadata': self.preserve_metadata.isChecked(),
            'border_color': self.border_color
        }

        # Create and start worker thread
        self.worker = ProcessWorker(self.selected_images, output_dir, settings)
        self.worker.progress.connect(lambda count, text: self.update_progress(progress, count, text))
        self.worker.finished.connect(lambda errors: self.process_complete(errors))
        self.worker.error.connect(lambda title, msg: QMessageBox.warning(self, title, msg))
        
        # Connect cancel button
        progress.canceled.connect(self.worker.stop)
        
        self.worker.start()

    def update_progress(self, progress_dialog, count, text):
        progress_dialog.setValue(count)
        progress_dialog.setLabelText(text)

    def process_complete(self, errors):
        if errors:
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Warning)
            error_msg.setWindowTitle("Processing Errors")
            error_msg.setText(f"Completed with {len(errors)} error(s):")
            error_msg.setDetailedText("\n".join(errors))
            error_msg.setStandardButtons(QMessageBox.Ok)
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            error_msg.exec_()
        else:
            QMessageBox.information(self, "Success", "All images processed successfully!")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def update_border_size_input(self, value):
        # Update the input field without triggering the textChanged signal
        self.border_size_input.blockSignals(True)
        self.border_size_input.setText(str(value))
        self.border_size_input.blockSignals(False)

    def on_border_size_input(self, text):
        if text:
            try:
                value = int(text)
                if 0 <= value <= 300:
                    self.border_slider.setValue(value)
            except ValueError:
                pass

    def show_thumbnails(self):
        if not self.selected_images:
            QMessageBox.information(self, "No Images", "Please add some images first.")
            return
            
        self.thumbnail_dialog = ThumbnailDialog(self, self.selected_images)
        self.thumbnail_dialog.show()

class ProcessWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str, str)

    def __init__(self, images, output_dir, settings):
        super().__init__()
        self.images = images
        self.output_dir = output_dir
        self.settings = settings
        self.should_stop = False

    def run(self):
        errors = []
        max_workers = min(os.cpu_count() or 1, len(self.images))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, image_path in enumerate(self.images):
                if self.should_stop:
                    break
                future = executor.submit(
                    self.process_single_image,
                    image_path,
                    i,
                    len(self.images)
                )
                futures.append(future)

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if self.should_stop:
                    break
                try:
                    error = future.result()
                    if error:
                        errors.append(error)
                except Exception as e:
                    errors.append(f"Unexpected error: {str(e)}")
                self.progress.emit(i + 1, f"Processed {i + 1} of {len(self.images)} images")

        self.finished.emit(errors)

    def process_single_image(self, image_path, index, total):
        try:
            # Extract settings
            base_filename = self.settings['base_filename']
            aspect_ratio = self.settings['aspect_ratio']
            border_size = self.settings['border_size']
            save_format = self.settings['save_format']
            quality = self.settings['quality']
            preserve_metadata = self.settings['preserve_metadata']
            border_color = self.settings['border_color']

            # Load and process image using PIL directly
            with Image.open(image_path) as img:
                # Preserve ICC profile if it exists
                icc_profile = img.info.get('icc_profile')
                
                # Convert to RGB if necessary, using better conversion
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, border_color)
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    else:
                        background.paste(img, mask=img.split()[1])  # Use alpha channel as mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate new dimensions
                orig_width, orig_height = img.size
                new_width, new_height = self.calculate_dimensions(
                    orig_width, orig_height, border_size, aspect_ratio
                )

                # Create new image with border
                result = Image.new('RGB', (new_width, new_height), border_color)
                paste_x = (new_width - orig_width) // 2
                paste_y = (new_height - orig_height) // 2
                result.paste(img, (paste_x, paste_y))

                # Handle file name
                if base_filename:
                    if total > 1:
                        base_name = f"{base_filename}_{index+1}"
                    else:
                        base_name = base_filename
                else:
                    original_name = os.path.basename(image_path)
                    base_name = os.path.splitext(original_name)[0] + "_processed"

                # Set appropriate extension
                if save_format == "JPEG":
                    ext = ".jpg"
                elif save_format == "TIFF":
                    ext = ".tiff"
                elif save_format == "PNG":
                    ext = ".png"
                elif save_format == "HEIF":
                    ext = ".heif"

                output_path = os.path.join(self.output_dir, base_name + ext)

                # Handle metadata
                exif_bytes = None
                if preserve_metadata:
                    try:
                        exif_dict = piexif.load(image_path)
                        gps_dict = exif_dict.get('GPS', {})
                        new_exif = {'GPS': gps_dict}
                        exif_bytes = piexif.dump(new_exif)
                    except:
                        pass

                # Save with appropriate format and quality
                save_args = {'format': save_format}
                
                if icc_profile:
                    save_args['icc_profile'] = icc_profile
                    
                if save_format == "JPEG":
                    save_args.update({
                        'quality': quality,
                        'exif': exif_bytes,
                        'optimize': True,
                        'subsampling': 0  # Disable chroma subsampling
                    })
                elif save_format == "HEIF":
                    save_args.update({'quality': quality})
                elif save_format == "PNG":
                    save_args.update({'optimize': True})
                    
                result.save(output_path, **save_args)
                
                return None

        except Exception as e:
            return f"Error processing {os.path.basename(image_path)}: {str(e)}"

    def calculate_dimensions(self, img_width, img_height, border_size, aspect_ratio):
        if aspect_ratio is None:
            new_width = img_width + (border_size * 2)
            new_height = img_height + (border_size * 2)
        else:
            target_ratio = aspect_ratio[0] / aspect_ratio[1]
            min_width = img_width + (border_size * 2)
            min_height = img_height + (border_size * 2)
            current_ratio = min_width / min_height
            
            if current_ratio > target_ratio:
                new_width = min_width
                new_height = int(new_width / target_ratio)
                new_height = max(new_height, min_height)
            else:
                new_height = min_height
                new_width = int(new_height * target_ratio)
                new_width = max(new_width, min_width)
        
        return new_width, new_height

    def stop(self):
        self.should_stop = True

def main():
    app = QApplication(sys.argv)
    window = ImageProcessor()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()