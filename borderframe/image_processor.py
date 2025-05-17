from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QSlider, QColorDialog, QLineEdit, QFrame, QCheckBox, QProgressDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIntValidator, QFont
import os
from .thumbnail_dialog import ThumbnailDialog
from .process_worker import ProcessWorker
from .utils import calculate_dimensions


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
        # Supported extensions: PNG, JPG, JPEG, BMP, GIF, TIFF, TIF, HEIF, HEIC
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.heif)"
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
                    if file.lower().endswith((
                        '.png',
                        '.jpg',
                        '.jpeg',
                        '.bmp',
                        '.gif',
                        '.tiff',
                        '.heif',
                    )):
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
        """Delegate to the shared utility implementation."""
        return calculate_dimensions(img_width, img_height, border_size, aspect_ratio)

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

