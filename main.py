import sys
from PyQt5.QtWidgets import QApplication

from borderframe.image_processor import ImageProcessor


def main():
    app = QApplication(sys.argv)
    window = ImageProcessor()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
