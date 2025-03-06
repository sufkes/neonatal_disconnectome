import sys

from PySide6.QtCore import Qt, Slot

from PySide6.QtGui import QPainter

from PySide6.QtWidgets import (QApplication, QFormLayout, QHeaderView,

                               QHBoxLayout, QLineEdit, QMainWindow,

                               QPushButton, QTableWidget, QTableWidgetItem,

                               QVBoxLayout, QWidget)

from PySide6.QtCharts import QChartView, QPieSeries, QChart
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tutorial")

if __name__ == "__main__":
    # Qt Application
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(800, 600)
    window.show()

    # Execute application
