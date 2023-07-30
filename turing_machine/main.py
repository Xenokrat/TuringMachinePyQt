import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt6.QtCore import pyqtSlot

from open import Ui_Form
from machine import TuringMachineGUI, TuringMachineApp


class OpenScreenGUI(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # connect
        self.ui.create_new_btn.clicked.connect(self.create_new)
        self.ui.load_btn.clicked.connect(self.load_state)
        self.ui.state_box.minimum = 1
        self.new_window = None

    def create_new(self):
        state_value = self.ui.state_box.value()
        alph_value = self.ui.alph_box.value()
        machine = TuringMachineApp(
            state_value=state_value,
            alph_value=alph_value,
        )
        self.new_window = TuringMachineGUI(machine=machine)
        self.new_window.open_requested.connect(self.show_again)
        self.new_window.show()
        self.hide()

    def load_state(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Save State",
            "./saved_states", "JSON Files (*.json);;All Files (*)"
        )
        with open(file_path, "r") as f:
            data = json.load(f)
        machine = TuringMachineApp(**data)
        # TODO: bad code
        table_data = machine.table_data
        self.new_window = TuringMachineGUI(machine=machine)
        self.new_window.machine.table_data = table_data
        self.new_window.open_requested.connect(self.show_again)
        self.new_window.populate_table()
        self.new_window.update_tape_graphics()
        self.new_window.show()
        self.hide()

    @pyqtSlot()
    def show_again(self):
        self.show()
        self.new_window.close()
        self.new_window = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenScreenGUI()
    window.show()
    sys.exit(app.exec())
