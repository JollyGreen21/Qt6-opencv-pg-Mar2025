import sys
# Remove incorrect path manipulation
# sys.path.append("opencv_pg/models/views")

import copy
import logging

import numpy as np
# Fix the incorrect import path
from views.widgets.slider_spinbox import DynamicSliderSpinBox

from PySide6 import QtWidgets, QtCore, QtGui

from views.widgets.sliders import (
    IntQSlider,
    FloatQSlider,
    SliderContainer,
    SliderPair,
)
from views.widgets.array import (
    ArrayEditor,
    ArrayEditorWithStructElement,
    ArraySize,
)
from .table_model import TableModel

log = logging.getLogger(__name__)


class Param:
    """Base class for all Transform Param's

    Args:
        default (any): The default value to use
        label (str, optional): The displayed label for this Param. Default is
            the class variable name will be used with `_` replaced by ` ` and
            each word capitalized.
        help_text (str, optional): Tooltip text to display when cursor is
            hovered over the Param's label. Default is ''.
    """

    def __init__(self, default=None, label=None, read_only=False, help_text=""):
        self._value = default
        super().__init__()
        self.label = label
        self._transform = None
        self.widget = None
        self.help_text = help_text
        self.read_only = read_only

    def _get_widget(self, parent=None):
        """Return widget for this Param

        This method must do the following:
        - instantiate a widget
        - connect some form of change handler to the appropriate 'change' signal
          of the widget
            - that change handler only needs to call self._store_value_and_start
              with the new value to store for the Param
        - return the widget
        """
        raise NotImplementedError

    def get_widget(self, parent=None):
        """Wrapper around _get_widget in case we need to do other work"""
        self.widget = self._get_widget(parent)
        return self.widget

    def set_enabled(self, enabled: bool):
        """Set whether this Param's widget/label are enabled

        Args:
            enabled (Boolean): True if enabled
        """
        lbl = self.widget.parent().form_layout.labelForField(self.widget)
        lbl.setEnabled(enabled)
        self.widget.setEnabled(enabled)

    def _store_value_and_start(self, value):
        """Store the changed value and run the pipeline

        Arguments:
            value (any): value to be stored in _value
        """
        if value is not None:
            self._value = value
            log.debug("%s: %s", self.__class__.__name__, value)
        if self._transform is not None:
            self._transform.start_pipeline()


class BaseSlider(Param):
    """Base class for Slider type Param's

    Args:
        min_val (Int, Float): Minimum acceptable value
        max_val (Int, Float): Maximum acceptable value
        step (Int, Float): Step size of the slider
        editable_range (Bool): If True, allows editing the min/max by double
            clicking the respective min/max label.
    """

    slider_class = None

    def __init__(
        self,
        min_val,
        max_val,
        default=None,
        step=1,
        label=None,
        editable_range=True,
        help_text="",
    ):
        super().__init__(default=default, label=label, help_text=help_text)
        self.min = min_val
        self.max = max_val
        self.default = default
        self.editable_range = editable_range
        self.step = step
        self._value = self._set_initial_value(default, min_val, max_val)

    def _set_initial_value(self, default, _min, _max):
        if default is None:
            return _min
        if _min <= default <= _max:
            return default
        raise ValueError(f"Default must be between {_min} and {_max}. Got {default}.")

    def _get_widget(self, parent=None):
        widget = self.slider_class(QtCore.Qt.Horizontal, parent=parent)
        widget.setMinimum(self.min)
        widget.setMaximum(self.max)
        widget.setInterval(self.step)
        
        # Use a lambda to ensure proper binding of the change handler.
        widget.valueChanged.connect(lambda value: self._handle_value_changed(value))
        
        container = SliderContainer(widget, editable_range=self.editable_range)
        
        # The container now has a value_spinbox instead of slider_text
        return container

    def set_step(self, step):
        """Change the step size for the slider"""
        self.widget.slider.setSingleStep(step)
        self.widget.slider.setInterval(step)

    def set_min(self, value):
        """Change the min value of the slider"""
        self.widget.min_label.setText(str(value))
        self.widget.slider.setMinimum(value)

    def set_max(self, value):
        """Change the max value of the slider"""
        # Convert any numeric type to appropriate type for the slider
        if isinstance(value, (float, np.float64, np.float32)):
            value = float(value)  # Ensure Python native float
        elif isinstance(value, (int, np.int64, np.int32)):
            value = int(value)    # Ensure Python native int
        
        self.widget.max_label.setText(str(value))
        self.widget.slider.setMaximum(value)

    def _handle_value_changed(self, value):
        """Runs the pipeline - subclasses override with @Slot and call super"""
        self._store_value_and_start(value)


class IntSlider(BaseSlider):
    """A slider that operates on Integers"""

    slider_class = IntQSlider

    @QtCore.Slot(int)
    def _handle_value_changed(self, value):
        super()._handle_value_changed(value)


class FloatSlider(BaseSlider):
    """A slider that operates on Floats"""

    slider_class = FloatQSlider

    @QtCore.Slot(float)
    def _handle_value_changed(self, value):
        super()._handle_value_changed(value)


class ComboBox(Param):
    """A ComboBox with options

    Args:
        options ([str]): Labels to select from. Displayed in the order supplied.
        options_map (dict): Dict of <label>: <real_value>. For example:
            {"BORDER_DEFAULT": cv2.BORDER_DEFAULT, ...}
        default (str): label from `options_map` to use as the default
    """

    def __init__(self, options, options_map, default=None, label=None, help_text=""):
        """A ComboBox with options"""
        super().__init__(label=label, default=default, help_text=help_text)
        self.options = options
        self.options_map = options_map
        self._value = self._set_initial_value(default, options_map)

    def _set_initial_value(self, default, values):
        """Sets the initial value first value if default is None, else default"""
        if default is None:
            return list(values.values())[0]
        if default not in self.options_map:
            raise KeyError(
                "default %s is not a valid choice in the options_map", default
            )
        return self.options_map[default]

    def _get_widget(self, parent=None):
        options_inverse = {v: k for k, v in self.options_map.items()}
        widget = QtWidgets.QComboBox(parent=parent)
        for item in self.options:
            widget.addItem(item)
        widget.setCurrentText(str(options_inverse[self._value]))  # Ensure the argument is a string
        # Use a lambda to pass the text to the handler
        widget.currentTextChanged.connect(lambda text: self._handle_value_changed(text))
        return widget

    @QtCore.Slot(str)
    def _handle_value_changed(self, value):
        self._store_value_and_start(self.options_map[value])


class ColorPicker(Param):
    """Adds a button and allows the user to select a color

    Args:
        default (uint8, uint8, uint8): Default color in RGB
    """

    def __init__(self, default=None, label=None, help_text=""):
        """Represents a Select Box"""
        super().__init__(label, help_text=help_text)
        self.default = default
        self._value = self._set_initial_value(self.default)

    def _set_initial_value(self, default):
        if default is None:
            return (255, 255, 255)
        if len(default) != 3:
            raise ValueError("default should be a 3-tuple from 0-255")
        for x in default:
            if 0 > x > 255:
                raise ValueError("default should be a 3-tuple from 0-255")
        return default

    def _get_widget(self, parent=None):
        btn = QtWidgets.QPushButton(text="Choose Color")
        btn.setIcon(self._get_color_icon())
        # Connect using lambda to adapt the parameters
        btn.clicked.connect(lambda checked: self._handle_clicked())
        return btn

    def _get_color_icon(self, x=10, y=10):
        """Return the current color as an RGB tuple"""
        pixmap = QtGui.QPixmap(x, y)
        b, g, r = self._value
        # Replace qRgb with QColor which is the expected type for fill()
        color = QtGui.QColor(r, g, b)
        return QtGui.QIcon(pixmap)

    @QtCore.Slot()
    def _handle_clicked(self):
        """Open color picker and store result. Picker is asssumed to be RGB"""
        initial = QtGui.QColor()
        b, g, r = self._value
        initial.setRgb(r, g, b, 255)
        color = QtWidgets.QColorDialog.getColor(initial=initial)
        if color.isValid():
            r, g, b, _ = color.getRgb()
            self._store_value_and_start((b, g, r))
            self.widget.setIcon(self._get_color_icon())


class ReadOnlyLabel(Param):
    """ReadOnlyLabel that displays its _value using fmt_str

    Args:
        fmt_str (str): format string using kwarg format where your variable
            is x, eg: 'your value: {x}' or 'val1: {x[0]}, val2: {x[1]}'
    """

    def __init__(self, fmt_str, default=None, label=None, help_text=""):
        super().__init__(default=default, label=label, help_text=help_text)
        self.fmt_str = fmt_str
        self._value = self._set_initial_value(default)

    def _set_initial_value(self, default):
        return default

    def _get_widget(self, parent=None):
        return QtWidgets.QLabel(str(self))

    def __str__(self):
        return self.fmt_str.format(x=self._value)


class SpinBox(Param):
    """A SpinBox Param"""

    def __init__(self, min_val, max_val, default=None, step=1, label=None, help_text=""):
        super().__init__(default=default, label=label, help_text=help_text)
        self.min = min_val
        self.max = max_val
        self.step = step

    def _get_widget(self, parent=None):
        is_float = not isinstance(self._value, int)
        widget = DynamicSliderSpinBox(self.min, self.max, self._value, self.step, is_float, parent)
        widget.valueChanged(lambda value: self._store_value_and_start(value))
        return widget


class CheckBox(Param):
    """A simple two-state CheckBox"""

    def __init__(self, default=None, label=None, help_text=""):
        super().__init__(default=default, label=label, help_text=help_text)
        self._value = self._set_initial_value(default)

    def _set_initial_value(self, default):
        if default is None:
            return False
        if not isinstance(default, bool):
            raise TypeError("CheckBox default must be bool, got %s", type(default))
        return default

    def _get_widget(self, parent=None):
        sb = QtWidgets.QCheckBox(parent=parent)
        sb.setCheckState(self._get_checked_state(self._value))
        # Wrap the slot to ensure it's bound correctly
        sb.stateChanged.connect(lambda value: self._handle_value_changed(value))
        return sb

    def _get_checked_state(self, value):
        """Return the appropriate QtCore.Qt.CheckState based on bool val"""
        if value:
            return QtCore.Qt.CheckState.Checked
        return QtCore.Qt.CheckState.Unchecked

    @QtCore.Slot(int)
    def _handle_value_changed(self, value):
        if value == QtCore.Qt.CheckState.Unchecked:
            value = False
        elif value == QtCore.Qt.CheckState.Checked:
            value = True
        # This handles PartiallyChecked
        else:
            value = None
        self._store_value_and_start(value)


class Dimensions2D(Param):
    """A set of two integer input value boxes

    Args:
        min_val (int): Minimum allowable value
        max_val (int): Maximum allowable value
        default ((int, int)): Default values for first and second boxes
        prefix (str, optional): Text in front of the two input boxes, like:
            <prefix>: [   ], [   ]
    """

    def __init__(
        self,
        min_val=150,
        max_val=800,
        default=(500, 500),
        label=None,
        help_text="",
        prefix="",
        read_only=False,
    ):
        super().__init__(
            default=default, label=label, help_text=help_text, read_only=read_only
        )
        self._value = self._set_initial_value(default)
        self.min = min_val
        self.max = max_val
        self.prefix = prefix

    def _set_initial_value(self, default):
        if (
            default is None
            or not isinstance(default, (tuple, list))
            or len(default) != 2
        ):
            raise ValueError(
                "Array Size default must be 2-tuple of ints, got {}".format(default)
            )
        return default

    def _get_widget(self, parent=None):
        widget = ArraySize(
            parent=parent, prefix=self.prefix, min_val=self.min, max_val=self.max
        )
        widget.set_text(*self._value)
        widget.valueChanged.connect(
            lambda width, height: self._handle_dimensions_changed(width, height)
        )
        return widget

    @QtCore.Slot(int, int)
    def _handle_value_changed(self, rows, cols):
        self._store_value_and_start((rows, cols))

    def _handle_dimensions_changed(self, width, height):
        """Handle when dimensions widget changes - it emits width and height"""
        self._store_value_and_start((width, height))


class Array(Param):
    """An editable 2D array of values

    Args:
        use_struct (bool, optional): Adds Structuring Element selection if True.
            Default is False.
        use_anchor (bool, optional): Allows right clicking to set an anchor if
            True. Default is True.
        default (ndarray, optional): Default value for array. Default is
            np.ones((3, 3)).
        editable_array (bool, optional): If False, array values cannot be
            edited. Default is True.
    """

    def __init__(
        self,
        use_struct=False,
        use_anchor=True,
        default=None,
        label=None,
        help_text="",
        editable_array=True,
        dims=2,
    ):
        super().__init__(default=default, label=label, help_text=help_text)
        self._value = self._set_initial_value(default, dims)
        if dims == 1:
            self.anchor = -1
        else:
            self.anchor = (-1, -1)
        self._use_anchor = use_anchor
        self._use_struct = use_struct
        self._editable_array = editable_array
        self.dims = dims

    def _set_initial_value(self, default, dims):
        if default is None:
            if dims == 1:
                return np.ones((1, 3))
            else:
                return np.ones((3, 3))
        if not isinstance(default, np.ndarray):
            raise ValueError("Matrix default must be a numpy array, got %s", type(default))
            raise ValueError("Matrix default must be a numpy array, got %s" % type(default))

    def _get_widget(self, parent=None):
        model = TableModel(np.ones(self._value.shape))
        if not self._editable_array:
            model.editable = False
        if self._use_struct:
            widget = ArrayEditorWithStructElement(
                use_anchor=self._use_anchor, model=model, parent=parent
            )
        else:
            widget = ArrayEditor(
                use_anchor=self._use_anchor, model=model, parent=parent, dims=self.dims
            )
        # Use lambda to bridge the signal-slot connection
        widget.valueChanged.connect(lambda array: self._handle_value_changed(array))
        if self._use_anchor:
            # Use lambda to bridge the signal-slot connection
            widget.anchorChanged.connect(lambda row, col: self._handle_anchor_changed(row, col))
        return widget

    # Remove the @QtCore.Slot decorator that's causing the type mismatch
    def _handle_value_changed(self, array):
        self._store_value_and_start(array)

    def _handle_anchor_changed(self, row, col):
        if self.dims == 1:
            self.anchor = col
        else:
            self.anchor = (row, col)
        self._transform.start_pipeline()


class SliderPairParam(Param):
    """A stacked pair of sliders

    Args:
        min_val (int): Minimum allowable value
        max_val (int): Maximum allowable value
        step (int, optional): Increment/Decrement size. Default is 1.
        editable_range (bool): Min/max can be edited by double clicking
            min/max labels if True. Default is True.
    """

    def __init__(
        self,
        min_val,
        max_val,
        default=None,
        step=1,
        label=None,
        editable_range=True,
        help_text="",
    ):
        super().__init__(default=default, label=label, help_text=help_text)
        self.min = min_val
        self.max = max_val
        self.default = default
        self.editable_range = editable_range
        self.step = step
        self._value = self._set_initial_value(default, min_val, max_val)

    def _set_initial_value(self, default, _min, _max):
        return {"top": _min, "bot": _max}

    def _get_widget(self, parent=None):
        slider1 = IntQSlider(QtCore.Qt.Horizontal, parent=parent)
        slider2 = IntQSlider(QtCore.Qt.Horizontal, parent=parent)
        self._setup_slider(slider1, self.min)
        self._setup_slider(slider2, self.max)
        widget = SliderPair(slider1, slider2, False)
        # Use lambda functions to bridge the signal-slot connection
        widget.topChanged.connect(lambda value: self._handle_top_changed(value))
        widget.botChanged.connect(lambda value: self._handle_bot_changed(value))
        return widget

    def _setup_slider(self, slider, default):
        slider.setMinimum(self.min)
        slider.setMaximum(self.max)
        slider.setInterval(self.step)
        # Removed as it does not exist

    def _handle_top_changed(self, value):
        v = copy.copy(self._value)
        v["top"] = value
        self._store_value_and_start(v)

    def _handle_bot_changed(self, value):
        v = copy.copy(self._value)
        v["bot"] = value
        self._store_value_and_start(v)


class NumberParam:
    def __init__(self, label, default_value=0, min_value=0, max_value=100, step=1):
        self.label = label
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def get_widget(self):
        widget = QtWidgets.QSpinBox()
        widget.setMinimum(self.min_value)
        widget.setMaximum(self.max_value)
        widget.setSingleStep(self.step)
        widget.setValue(self.default_value)
        return widget
