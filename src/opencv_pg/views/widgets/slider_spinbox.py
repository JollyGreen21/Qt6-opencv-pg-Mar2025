from PySide6 import QtWidgets, QtCore

class DynamicSliderSpinBox(QtWidgets.QWidget):
    def __init__(self, min_val, max_val, default=None, step=1, is_float=False, parent=None):
        super().__init__(parent)
        self.is_float = is_float

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setSingleStep(step)
        self.slider.setValue(default)

        if is_float:
            self.spin_box = QtWidgets.QDoubleSpinBox(self)
            self.spin_box.setDecimals(2)
            self.spin_box.setSingleStep(step)
        else:
            self.spin_box = QtWidgets.QSpinBox(self)
            self.spin_box.setSingleStep(step)

        self.spin_box.setMinimum(min_val)
        self.spin_box.setMaximum(max_val)
        self.spin_box.setValue(default)

        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.spin_box)

        self.slider.valueChanged.connect(self._sync_spin_box)
        self.spin_box.valueChanged.connect(self._sync_slider)

    def _sync_spin_box(self, value):
        if self.is_float:
            self.spin_box.setValue(value / 100.0)
        else:
            self.spin_box.setValue(value)

    def _sync_slider(self, value):
        if self.is_float:
            self.slider.setValue(int(value * 100))
        else:
            self.slider.setValue(value)

    def value(self):
        return self.spin_box.value()

    def setValue(self, value):
        self.slider.setValue(value)
        self.spin_box.setValue(value)

    def setMinimum(self, value):
        self.slider.setMinimum(value)
        self.spin_box.setMinimum(value)

    def setMaximum(self, value):
        self.slider.setMaximum(value)
        self.spin_box.setMaximum(value)

    def setSingleStep(self, value):
        self.slider.setSingleStep(value)
        self.spin_box.setSingleStep(value)

    def valueChanged(self, callback):
        self.slider.valueChanged.connect(callback)
        self.spin_box.valueChanged.connect(callback)