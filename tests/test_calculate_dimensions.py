import types
import sys

# Stub PyQt5 modules so main.py can be imported without PyQt5 installed
qtwidgets = types.ModuleType('PyQt5.QtWidgets')
for cls in [
    'QApplication', 'QMainWindow', 'QPushButton', 'QFileDialog', 'QVBoxLayout',
    'QHBoxLayout', 'QWidget', 'QLabel', 'QComboBox', 'QSlider', 'QColorDialog',
    'QScrollArea', 'QGridLayout', 'QLineEdit', 'QFrame', 'QSizePolicy',
    'QCheckBox', 'QProgressDialog', 'QMessageBox', 'QDialog'
]:
    setattr(qtwidgets, cls, type(cls, (), {}))

qtcore = types.ModuleType('PyQt5.QtCore')
for cls in ['Qt', 'QTimer', 'QSize', 'QThread', 'QObject']:
    setattr(qtcore, cls, type(cls, (), {}))
# pyqtSignal is called at import time; use callable stub
def pyqtSignal(*args, **kwargs):
    return None
qtcore.pyqtSignal = pyqtSignal

qtgui = types.ModuleType('PyQt5.QtGui')
for cls in ['QPixmap', 'QImage', 'QPainter', 'QColor', 'QIntValidator', 'QFont']:
    setattr(qtgui, cls, type(cls, (), {}))

sys.modules.setdefault('PyQt5', types.ModuleType('PyQt5'))
sys.modules['PyQt5.QtWidgets'] = qtwidgets
sys.modules['PyQt5.QtCore'] = qtcore
sys.modules['PyQt5.QtGui'] = qtgui

# Stub PIL and numpy modules
pil_module = types.ModuleType('PIL')
sys.modules['PIL'] = pil_module
sys.modules['PIL.Image'] = types.ModuleType('PIL.Image')
exif_tags = types.ModuleType('PIL.ExifTags')
exif_tags.TAGS = {}
sys.modules['PIL.ExifTags'] = exif_tags
sys.modules['piexif'] = types.ModuleType('piexif')
sys.modules['numpy'] = types.ModuleType('numpy')

from main import ImageProcessor


def get_processor():
    # instantiate without calling __init__ to avoid Qt requirements
    return ImageProcessor.__new__(ImageProcessor)


def test_no_aspect_ratio_adds_border_only():
    proc = get_processor()
    assert proc.calculate_dimensions(100, 80, 10, None) == (120, 100)


def test_square_ratio_landscape_image():
    proc = get_processor()
    width, height = proc.calculate_dimensions(100, 50, 10, (1, 1))
    assert (width, height) == (120, 120)


def test_square_ratio_portrait_image():
    proc = get_processor()
    width, height = proc.calculate_dimensions(50, 100, 5, (1, 1))
    assert (width, height) == (110, 110)


def test_four_by_five_ratio_various_size():
    proc = get_processor()
    width1, height1 = proc.calculate_dimensions(800, 600, 10, (4, 5))
    assert (width1, height1) == (820, 1025)
    width2, height2 = proc.calculate_dimensions(100, 200, 0, (4, 5))
    assert (width2, height2) == (160, 200)
