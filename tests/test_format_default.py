import types
import sys

# Stub PyQt5 modules for headless testing
qtwidgets = types.ModuleType('PyQt5.QtWidgets')

class QComboBox:
    def __init__(self):
        self.items = []
        self.current_index = -1
    def addItems(self, items):
        self.items.extend(items)
    def setCurrentIndex(self, index):
        self.current_index = index
    def currentText(self):
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return ""
    def findText(self, text):
        try:
            return self.items.index(text)
        except ValueError:
            return -1
    def setToolTip(self, *_):
        pass

for cls in [
    'QApplication', 'QMainWindow', 'QPushButton', 'QFileDialog', 'QVBoxLayout',
    'QHBoxLayout', 'QWidget', 'QLabel', 'QSlider', 'QColorDialog',
    'QScrollArea', 'QGridLayout', 'QLineEdit', 'QFrame', 'QSizePolicy',
    'QCheckBox', 'QProgressDialog', 'QMessageBox', 'QDialog'
]:
    setattr(qtwidgets, cls, type(cls, (), {}))
qtwidgets.QComboBox = QComboBox

qtcore = types.ModuleType('PyQt5.QtCore')
for cls in ['Qt', 'QTimer', 'QSize', 'QThread', 'QObject']:
    setattr(qtcore, cls, type(cls, (), {}))
qtcore.pyqtSignal = lambda *a, **k: None

qtgui = types.ModuleType('PyQt5.QtGui')
for cls in ['QPixmap', 'QImage', 'QPainter', 'QColor', 'QIntValidator', 'QFont']:
    setattr(qtgui, cls, type(cls, (), {}))

sys.modules.setdefault('PyQt5', types.ModuleType('PyQt5'))
sys.modules['PyQt5.QtWidgets'] = qtwidgets
sys.modules['PyQt5.QtCore'] = qtcore
sys.modules['PyQt5.QtGui'] = qtgui

# Stub other modules
sys.modules['PIL'] = types.ModuleType('PIL')
sys.modules['PIL.Image'] = types.ModuleType('PIL.Image')
sys.modules['PIL.ImageOps'] = types.ModuleType('PIL.ImageOps')
imageqt_module = types.ModuleType('PIL.ImageQt')
imageqt_module.ImageQt = type('ImageQt', (), {})
sys.modules['PIL.ImageQt'] = imageqt_module
exif_tags = types.ModuleType('PIL.ExifTags')
exif_tags.TAGS = {}
sys.modules['PIL.ExifTags'] = exif_tags
sys.modules['piexif'] = types.ModuleType('piexif')
sys.modules['numpy'] = types.ModuleType('numpy')

from borderframe.image_processor import ImageProcessor


def get_processor():
    proc = ImageProcessor.__new__(ImageProcessor)
    proc.selected_images = []
    proc.format_combo = QComboBox()
    proc.save_formats = {
        "Select format...": (None, None),
        "JPEG (80% quality)": ("JPEG", 80),
        "JPEG (95% quality)": ("JPEG", 95),
        "JPEG (100% quality)": ("JPEG", 100),
        "TIFF": ("TIFF", None),
        "PNG": ("PNG", None),
        "HEIF (80% quality)": ("HEIF", 80),
        "HEIF (95% quality)": ("HEIF", 95),
        "HEIF (100% quality)": ("HEIF", 100)
    }
    proc.format_combo.addItems(proc.save_formats.keys())
    return proc


def test_default_format_jpeg():
    proc = get_processor()
    proc.selected_images = ["a.jpg", "b.JPG"]
    proc.update_format_default()
    assert proc.format_combo.currentText() == "JPEG (100% quality)"


def test_default_format_mixed():
    proc = get_processor()
    proc.selected_images = ["a.jpg", "b.png"]
    proc.update_format_default()
    assert proc.format_combo.currentText() == "Select format..."
