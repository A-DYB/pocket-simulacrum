import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui

import json

from enemy import Enemy
from weapon import Weapon


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SimPy v1.0")

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)
        self.SP_health_buff_spinner = QtWidgets.QDoubleSpinBox()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.SP_health_buff_spinner)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))


#   not a good function
def add_custom_enemy(name, health_type, shield_type, armor_type, base_health, base_shield, base_armor, base_level = 1):
    with open('./enemies.json') as f:
        data = json.load(f)
    if data[name]:
        print("Error: Enemy already exists")
        return

    data[name] = {}
    data[name][health_type] = health_type
    data[name][shield_type] = shield_type
    data[name][armor_type] = armor_type

    data[name][base_health] = base_health
    data[name][base_shield] = base_shield
    data[name][base_armor] = base_armor
    data[name][base_level] = base_level


def get_dark_palette():
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("black"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("white"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("white"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("white"))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("red"))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("black"))
    return palette


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    app.setPalette(get_dark_palette())

    widget = Window()
    widget.resize(800, 600)
    widget.show()
    enemy = Enemy("Gokstad Officer", 100, widget)
    print(enemy.armor_type)

    sys.exit(app.exec())
