import sys
import json
from time import sleep
from dataclasses import dataclass, asdict, field
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtCore import (
    Qt, QRectF, QThread, QMutex, QMutexLocker, pyqtSignal
)
from PyQt6.QtGui import QFont

from machine_ui import Ui_MainWindow


@dataclass
class TuringMachineApp:
    state_value: int
    alph_value: int
    is_ready_to_start: bool = True
    is_on: bool = False
    current_table_state: int = 1
    table_data: list[list[str]] = field(default_factory=list)
    tape: list[str] = field(default_factory=lambda: ["_"] * 30)
    current_tape_cell: int = 15
    mutex = QMutex()

    def __parse_command(self, command: str) -> tuple[str, int, int]:
        move_list = {"L": -1, "S": 0, "R": 1}
        raw_val, raw_move, raw_next = command.split(" ")
        val = self.tape[self.current_tape_cell] if raw_val == "N" else raw_val
        move = move_list[raw_move]
        next = int(raw_next[1:])
        return val, move, next

    def __update_machine_state(self, val: str, move: int, next: int) -> None:
        self.tape[self.current_tape_cell] = val
        self.current_tape_cell += move
        self.check_tape_expantion()
        self.current_table_state = next

    def check_tape_expantion(self) -> None:
        if self.current_tape_cell + 1 >= len(self.tape):
            self.tape.extend(["_"] * 10)
        elif self.current_tape_cell <= 0:
            self.tape = ["_"] * 10 + self.tape
            self.current_tape_cell += 10
        else:
            return

    def single_step(self) -> bool:
        with QMutexLocker(self.mutex):
            current_tape_cell_val = self.tape[self.current_tape_cell]
            if current_tape_cell_val == "_":
                columns_inx = 0
            else:
                columns_inx = int(current_tape_cell_val) + 1

            command = self.\
                table_data[self.current_table_state - 1][columns_inx]

            val, move, next = self.__parse_command(command)
            self.__update_machine_state(val, move, next)
            if next == 0:
                self.current_table_state = 1
                return False
            return True

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            data = json.dumps(asdict(self))
            f.writelines(data)


class TuringMachineGUI(QMainWindow):
    open_requested = pyqtSignal()

    def __init__(self, machine: TuringMachineApp) -> None:
        super().__init__()
        self.setWindowTitle("Turing Machine Array")
        self.setGeometry(100, 100, 800, 600)
        self.cell_size = 150

        self.machine = machine
        self.worker = Worker(self.machine)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.create_ui()

        # Adding Parsed Tables
        self.parse_table_values()

        # connect
        self.ui.set_empty_btn.clicked.connect(self.set_empty_value)
        self.ui.cell_val_btn.clicked.connect(self.set_cell_value)
        self.ui.table_widget.cellChanged.connect(self.parse_table_values)
        self.ui.one_step_btn.clicked.connect(self.exec_single_step)
        self.ui.many_steps_btn.clicked.connect(self.exec_many_steps)
        self.ui.stop_btn.clicked.connect(self.stop_exec)
        self.ui.save_state_btn.clicked.connect(self.save_state)
        self.ui.load_state_btn.clicked.connect(self.load_state)
        self.ui.new_machine_btn.clicked.connect(self.open_requested.emit)

        self.worker.signal.connect(self.update_tape_graphics)
        self.worker.btn_signal.connect(self.__release_buttons_after_loop)

        # draw tape
        self.update_tape_graphics()
        # mouse events
        self.ui.graphics_view.mousePressEvent = self.on_mouse_clicked

    def create_ui(self) -> None:
        self.ui.table_widget.setColumnCount(self.machine.alph_value + 1)
        self.ui.table_widget.setRowCount(self.machine.state_value)
        self.ui.table_widget.horizontalHeaderItem(0).setText("_")

        # Set upper limit for alph
        self.ui.cell_value_box.setMaximum(self.machine.alph_value - 1)

        for i in range(self.machine.alph_value):
            item = QTableWidgetItem()
            self.ui.table_widget.setHorizontalHeaderItem(i + 1, item)
            self.ui.table_widget.horizontalHeaderItem(i + 1).setText(str(i))

        for i in range(self.machine.state_value):
            item = QTableWidgetItem()
            self.ui.table_widget.setVerticalHeaderItem(i, item)
            self.ui.table_widget. \
                verticalHeaderItem(i).setText(f"Q{str(i + 1)}")

        # Algo table validation
        self.allowed_val_set = {"N", "_"}
        self.allowed_val_set.update(
            map(lambda x: str(x), range(self.machine.alph_value))
        )
        self.allowed_move_set = {"L", "R", "S"}
        self.allowd_next_step_set = {
            'Q' + str(i) for i in range(self.machine.state_value + 1)
        }

    def update_tape_graphics(self):
        with QMutexLocker(self.machine.mutex):
            scene = QGraphicsScene()
            for ind, value in enumerate(self.machine.tape):
                rect_item = QGraphicsRectItem(
                    ind * self.cell_size,
                    0,
                    self.cell_size,
                    self.cell_size,
                )
                if ind == self.machine.current_tape_cell:
                    rect_item.setBrush(Qt.GlobalColor.red)
                else:
                    rect_item.setBrush(
                        Qt.GlobalColor.gray if value != "_"
                        else Qt.GlobalColor.black
                    )
                scene.addItem(rect_item)

                # add digits
                text_item = QGraphicsTextItem(str(value))
                item_font = QFont("Times New Roman", 40)
                item_font.setBold(True)
                text_item.setFont(item_font)
                text_item.adjustSize()
                text_item.setPos(
                    ind * self.cell_size + self.cell_size/2 -
                    text_item.boundingRect().width()/2,
                    self.cell_size/2 - text_item.boundingRect().height()/2
                )
                scene.addItem(text_item)

            self.ui.graphics_view.setScene(scene)

    def set_empty_value(self):
        self.machine.tape[self.machine.current_tape_cell] = "_"
        self.update_tape_graphics()

    def set_cell_value(self):
        new_value = self.ui.cell_value_box.value()
        self.machine.tape[self.machine.current_tape_cell] = new_value
        self.update_tape_graphics()

    def on_mouse_clicked(self, event):
        pos = event.pos()
        scene_pos = self.ui.graphics_view.mapToScene(pos)
        for ind, value in enumerate(self.machine.tape):
            rect = QRectF(
                ind * self.cell_size, 0, self.cell_size, self.cell_size
            )
            if rect.contains(scene_pos):
                self.machine.current_tape_cell = ind
                self.machine.check_tape_expantion()
                self.update_tape_graphics()

    def parse_table_values(self) -> None:
        table_data = []
        for row in range(self.ui.table_widget.rowCount()):
            row_data = []
            for col in range(self.ui.table_widget.columnCount()):
                item = self.ui.table_widget.item(row, col)
                if item is not None:
                    cell_value = item.text()
                    row_data.append(cell_value)
                else:
                    row_data.append("")
            table_data.append(row_data)
        self.machine.table_data = table_data

    def populate_table(self) -> None:
        for row_num, row_val in enumerate(self.machine.table_data):
            for col_num, cell_val in enumerate(row_val):
                self.ui.table_widget.setItem(
                    row_num, col_num, QTableWidgetItem(cell_val)
                )

    def __validate_table(self):
        self.machine.is_ready_to_start = True
        for row, row_val in enumerate(self.machine.table_data):
            for col, cell_val in enumerate(row_val):
                self.__validate_table_cell(cell_val, row, col)

    def __validate_table_cell(
        self, cell_value: str, row: int, col: int
    ) -> None:
        col_msg = str(col - 1) if col > 0 else "_"
        row_msg = row + 1
        try:
            val_change, move, step = cell_value.split(" ")
        except ValueError:
            QMessageBox.critical(
                self, "Fail",
                f"Wrong number of arguments, cell {col_msg}-Q{row_msg}"
            )
            self.machine.is_ready_to_start = False
            return

        if val_change not in self.allowed_val_set:
            QMessageBox.critical(
                self, "Fail",
                f"Wrong new value {val_change}, cell {col_msg}-Q{row_msg}"
            )
            self.machine.is_ready_to_start = False
            return
        if move not in self.allowed_move_set:
            QMessageBox.critical(
                self, "Fail",
                f"Wrong move value {move}, cell {col_msg}-Q{row_msg}"
            )
            self.machine.is_ready_to_start = False
            return
        if step not in self.allowd_next_step_set:
            QMessageBox.critical(
                self, "Fail",
                f"Wrong next step value {step}, cell {col_msg}-Q{row_msg}"
            )
            self.machine.is_ready_to_start = False
            return

    def exec_single_step(self) -> None:
        self.__validate_table()
        if not self.machine.is_ready_to_start:
            QMessageBox.critical(self, "Fail", "Errors in Table")
            return
        self.machine.single_step()
        self.update_tape_graphics()

    def __block_buttons_during_loop(self) -> None:
        self.ui.set_empty_btn.setEnabled(False)
        self.ui.cell_val_btn.setEnabled(False)
        self.ui.one_step_btn.setEnabled(False)
        self.ui.many_steps_btn.setEnabled(False)
        self.ui.save_state_btn.setEnabled(False)
        self.ui.load_state_btn.setEnabled(False)
        self.ui.cell_value_box.setEnabled(False)
        self.ui.step_pause.setEnabled(False)

    def __release_buttons_after_loop(self) -> None:
        self.ui.set_empty_btn.setEnabled(True)
        self.ui.cell_val_btn.setEnabled(True)
        self.ui.one_step_btn.setEnabled(True)
        self.ui.many_steps_btn.setEnabled(True)
        self.ui.save_state_btn.setEnabled(True)
        self.ui.load_state_btn.setEnabled(True)
        self.ui.cell_value_box.setEnabled(True)
        self.ui.step_pause.setEnabled(True)

    def exec_many_steps(self) -> None:
        delay = self.ui.step_pause.value()
        self.worker.delay = delay
        self.__validate_table()
        if not self.machine.is_ready_to_start:
            QMessageBox.critical(self, "Fail", "Errors in Table")
            return
        self.__block_buttons_during_loop()
        if not self.worker.isRunning():
            self.worker.start()

    def stop_exec(self) -> None:
        if self.worker.isRunning():
            self.worker.stop()

    def save_state(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save State",
            "./saved_states", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
        self.machine.save_to_file(file_path)

    def load_state(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Save State",
            "./saved_states", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
        with open(file_path, "r") as f:
            data = json.load(f)
        self.machine = TuringMachineApp(**data)
        self.worker.machine = self.machine
        self.create_ui()
        self.populate_table()
        self.update_tape_graphics()


class Worker(QThread):
    signal = pyqtSignal()
    btn_signal = pyqtSignal()

    def __init__(self, machine: TuringMachineApp) -> None:
        super().__init__()
        self.machine = machine
        self.running = False
        self.delay = 1.0

    def run(self) -> None:
        self.running = True
        while self.running:
            if self.machine.single_step():
                self.signal.emit()
                sleep(self.delay)
            else:
                self.signal.emit()
                self.stop()

    def stop(self) -> None:
        self.running = False
        self.machine.current_table_state = 1
        self.btn_signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TuringMachineGUI()
    window.show()
    sys.exit(app.exec())
