import sys
from dataclasses import dataclass, asdict, field
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
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont

from machine_ui import Ui_MainWindow


class TableValueError(Exception):
    pass


@dataclass
class TuringMachineApp:
    state_value: int
    alph_value: int
    is_ready_to_start: bool = True
    is_on: bool = False
    current_table_state: int = 1
    table_data: list[list[str]] = field(default_factory=list)
    tape: list[str] = field(default_factory=lambda: [""] * 30)
    current_tape_cell: int = 15

    def __parse_command(self, command: str) -> tuple[str, int, int]:
        move_list = {"L": -1, "S": 0, "R": 1}
        raw_val, raw_move, raw_next = command.split(" ")
        val = self.tape[self.current_tape_cell] if raw_val == "N" else raw_val
        move = move_list[raw_move]
        next = int(raw_next[1:])
        return val, move, next

    def update_machine_state(self, val: str, move: int, next: int) -> None:
        self.tape[self.current_tape_cell] = val
        self.current_tape_cell += move
        self.current_table_state = next

    def single_step(self) -> None:
        current_tape_cell_val = self.tape[self.current_tape_cell]
        if current_tape_cell_val == "":
            columns_inx = 0
        else:
            columns_inx = int(current_tape_cell_val) + 1
        print(f"columns_inx {columns_inx}")
        print(f"table {self.table_data}")
        command = self.table_data[self.current_table_state - 1][columns_inx]
        val, move, next = self.__parse_command(command)
        self.update_machine_state(val, move, next)

    def many_steps(self) -> None:
        pass


class TuringMachineGUI(QMainWindow):
    def __init__(self, machine: TuringMachineApp) -> None:
        super().__init__()
        self.setWindowTitle("Turing Machine Array")
        self.setGeometry(100, 100, 800, 600)
        self.cell_size = 100

        self.machine = machine

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.table_widget.setColumnCount(self.machine.alph_value + 1)
        self.ui.table_widget.setRowCount(self.machine.state_value)
        self.ui.table_widget.horizontalHeaderItem(0).setText("_")

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

        # Adding Parsed Tables
        self.parse_table_values()

        # connect
        self.ui.push_left_btn.clicked.connect(self.step_left)
        self.ui.push_right_btn.clicked.connect(self.step_right)
        self.ui.set_empty_btn.clicked.connect(self.set_empty_value)
        self.ui.cell_val_btn.clicked.connect(self.set_cell_value)
        self.ui.table_widget.cellChanged.connect(self.parse_table_values)
        self.ui.one_step_btn.clicked.connect(self.exec_single_step)
        # draw tape
        self.update_tape_graphics()
        # mouse events
        self.ui.graphics_view.mousePressEvent = self.on_mouse_clicked

    def update_tape_graphics(self):
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
                    Qt.GlobalColor.gray if value != ""
                    else Qt.GlobalColor.black
                )
            scene.addItem(rect_item)

            # add digits
            text_item = QGraphicsTextItem(str(value))
            text_item.setPos(
                ind * self.cell_size + self.cell_size/2 -
                text_item.boundingRect().width()/2,
                self.cell_size/2 - text_item.boundingRect().height()/2
            )
            text_item.setFont(QFont("Times New Roman", 15))
            scene.addItem(text_item)

        self.ui.graphics_view.setScene(scene)

    def step_left(self):
        self.machine.current_tape_cell -= 1
        self.update_tape_graphics()

    def step_right(self):
        self.machine.current_tape_cell += 1
        self.update_tape_graphics()

    def set_empty_value(self):
        self.machine.tape[self.machine.current_tape_cell] = ""
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
                self.update_tape_graphics()

    def parse_table_values(self) -> None:
        table_data = []
        self.machine.is_ready_to_start = True
        for row in range(self.ui.table_widget.rowCount()):
            row_data = []
            for col in range(self.ui.table_widget.columnCount()):
                item = self.ui.table_widget.item(row, col)
                if item is not None:
                    cell_value = item.text()
                    self.__validate_table_cell(cell_value, row, col)
                    row_data.append(cell_value)
                else:
                    row_data.append("")
            table_data.append(row_data)
        self.machine.table_data = table_data

    def __validate_table_cell(
        self, cell_value: str, row: int, col: int
    ) -> None:
        col_msg = str(col - 1) if col > 0 else "_"
        row_msg = row + 1
        if cell_value == '':
            return
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
        if not self.machine.is_ready_to_start:
            QMessageBox.critical(self, "Fail", "Errors in Table")
            return
        self.machine.single_step()
        self.update_tape_graphics()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TuringMachineGUI()
    window.show()
    sys.exit(app.exec())
