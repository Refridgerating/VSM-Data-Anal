import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QDockWidget,
    QWidget,
    QFormLayout,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QAction,
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class PlotControlsDock(QDockWidget):
    """Dock widget containing controls for the active plot."""

    def __init__(self, parent=None, apply_callback=None):
        super().__init__("Plot Controls", parent)
        self.apply_callback = apply_callback

        container = QWidget()
        form = QFormLayout(container)
        self.xmin = self._make_spinbox()
        self.xmax = self._make_spinbox()
        self.ymin = self._make_spinbox()
        self.ymax = self._make_spinbox()
        form.addRow("X min", self.xmin)
        form.addRow("X max", self.xmax)
        form.addRow("Y min", self.ymin)
        form.addRow("Y max", self.ymax)

        self.grid_cb = QCheckBox("Grid")
        self.minor_cb = QCheckBox("Minor Ticks")
        form.addRow(self.grid_cb)
        form.addRow(self.minor_cb)

        self.linewidth_combo = QComboBox()
        for w in [0.5, 1, 1.5, 2, 2.5, 3]:
            self.linewidth_combo.addItem(str(w), w)
        self.marker_combo = QComboBox()
        for m in ["None", "o", "x", "s", "^"]:
            self.marker_combo.addItem(m)
        self.linestyle_combo = QComboBox()
        for ls in ["solid", "dashed", "dashdot", "dotted", "None"]:
            self.linestyle_combo.addItem(ls)
        form.addRow("Linewidth", self.linewidth_combo)
        form.addRow("Marker", self.marker_combo)
        form.addRow("Linestyle", self.linestyle_combo)

        self.setWidget(container)

        widgets = [
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.grid_cb,
            self.minor_cb,
            self.linewidth_combo,
            self.marker_combo,
            self.linestyle_combo,
        ]
        for w in widgets:
            if isinstance(w, QDoubleSpinBox):
                w.valueChanged.connect(self._emit)
                w.lineEdit().editingFinished.connect(self._emit)
            elif isinstance(w, (QCheckBox, QComboBox)):
                w.stateChanged.connect(self._emit) if isinstance(w, QCheckBox) else w.currentIndexChanged.connect(self._emit)

    def _make_spinbox(self) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(-1e6, 1e6)
        sb.setDecimals(3)
        sb.setSpecialValueText("")
        sb.setValue(sb.minimum())
        sb.lineEdit().clear()
        return sb

    def limits(self):
        def val(sb: QDoubleSpinBox):
            text = sb.lineEdit().text().strip()
            return float(text) if text else None

        return val(self.xmin), val(self.xmax), val(self.ymin), val(self.ymax)

    def _emit(self):
        if self.apply_callback:
            self.apply_callback()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot Controls Demo")
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)

        x = np.linspace(0, 10, 200)
        self.line, = self.ax.plot(x, np.sin(x))

        self.controls = PlotControlsDock(self, self.apply_settings)
        self.addDockWidget(Qt.RightDockWidgetArea, self.controls)

        view_menu = self.menuBar().addMenu("View")
        self.controls_action = QAction("Plot Controls", self, checkable=True)
        self.controls_action.setChecked(True)
        self.controls_action.triggered.connect(self.controls.setVisible)
        self.controls.visibilityChanged.connect(self.controls_action.setChecked)
        view_menu.addAction(self.controls_action)

        self.apply_settings()

    def apply_settings(self):
        xmin, xmax, ymin, ymax = self.controls.limits()
        if xmin is not None and xmax is not None:
            self.ax.set_xlim(xmin, xmax)
        else:
            self.ax.set_autoscalex_on(True)

        if ymin is not None and ymax is not None:
            self.ax.set_ylim(ymin, ymax)
        else:
            self.ax.set_autoscaley_on(True)

        self.ax.grid(self.controls.grid_cb.isChecked())
        if self.controls.minor_cb.isChecked():
            self.ax.minorticks_on()
        else:
            self.ax.minorticks_off()

        lw = self.controls.linewidth_combo.currentData()
        if lw is not None:
            self.line.set_linewidth(lw)
        marker = self.controls.marker_combo.currentText()
        self.line.set_marker("" if marker == "None" else marker)
        ls = self.controls.linestyle_combo.currentText()
        if ls == "None":
            self.line.set_linestyle("")
        else:
            self.line.set_linestyle(ls)

        self.canvas.draw_idle()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
