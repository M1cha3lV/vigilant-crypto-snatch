import sys

from PyQt6.QtWidgets import QApplication

from .control.main import MainWindowController
from .ui.main import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    controller = MainWindowController(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
