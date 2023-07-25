import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QVBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont

from open import Ui_Form
from machine import TuringMachineGUI, TuringMachineApp


class OpenScreenGUI(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # connect
        self.ui.create_new_btn.clicked.connect(self.create_new)
        self.ui.create_new_btn.clicked.connect(self.close)
        # draw tape
        # mouse events

    def create_new(self):
        state_value = self.ui.state_box.value()
        alph_value = self.ui.alph_box.value()
        machine = TuringMachineApp(
            state_value=state_value,
            alph_value=alph_value,
        )
        new_window = TuringMachineGUI(machine=machine)
        new_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenScreenGUI()
    window.show()
    sys.exit(app.exec())
