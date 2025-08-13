from __future__ import annotations

import ast
from pathlib import Path
import sys

QT_MAP = {
    # QtWidgets
    "QMainWindow": "QtWidgets",
    "QWidget": "QtWidgets",
    "QApplication": "QtWidgets",
    "QDialog": "QtWidgets",
    "QDialogButtonBox": "QtWidgets",
    "QFileDialog": "QtWidgets",
    "QMessageBox": "QtWidgets",
    "QMenu": "QtWidgets",
    "QMenuBar": "QtWidgets",
    "QToolBar": "QtWidgets",
    "QDockWidget": "QtWidgets",
    "QVBoxLayout": "QtWidgets",
    "QHBoxLayout": "QtWidgets",
    "QFormLayout": "QtWidgets",
    "QGridLayout": "QtWidgets",
    "QSplitter": "QtWidgets",
    "QLabel": "QtWidgets",
    "QLineEdit": "QtWidgets",
    "QDoubleSpinBox": "QtWidgets",
    "QSpinBox": "QtWidgets",
    "QComboBox": "QtWidgets",
    "QCheckBox": "QtWidgets",
    "QPushButton": "QtWidgets",
    "QTableWidget": "QtWidgets",
    "QTableWidgetItem": "QtWidgets",
    "QHeaderView": "QtWidgets",
    # QtGui
    "QAction": "QtGui",
    "QIcon": "QtGui",
    "QKeySequence": "QtGui",
    "QCloseEvent": "QtGui",
    "QGuiApplication": "QtGui",
    # QtCore
    "Qt": "QtCore",
    "QTimer": "QtCore",
    "QSettings": "QtCore",
    "QSize": "QtCore",
    "QPoint": "QtCore",
    "QRect": "QtCore",
    "QObject": "QtCore",
    "pyqtSignal": "QtCore",
    "pyqtSlot": "QtCore",
    "QCoreApplication": "QtCore",
}

BASE = Path(__file__).resolve().parent.parent / "src" / "vsm_gui"


def check_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("PyQt6."):
            module = node.module.split(".")[-1]
            for alias in node.names:
                imported[alias.name] = module
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    errors: list[str] = []
    for name, module in imported.items():
        expected = QT_MAP.get(name)
        if expected and expected != module:
            errors.append(f"{path}: {name} imported from {module}, expected {expected}")
    for name, expected in QT_MAP.items():
        if name in used and imported.get(name) != expected:
            if name not in imported:
                errors.append(f"{path}: {name} used but not imported")
    return errors


def main() -> None:
    errors: list[str] = []
    for file in BASE.rglob("*.py"):
        errors.extend(check_file(file))
    if errors:
        print("Qt import issues found:")
        for err in errors:
            print(" -", err)
        sys.exit(1)
    print("All Qt imports look good.")


if __name__ == "__main__":
    main()
