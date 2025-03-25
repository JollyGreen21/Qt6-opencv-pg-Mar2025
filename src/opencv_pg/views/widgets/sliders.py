import logging

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QStyle
from utils.config_manager import config

log = logging.getLogger(__name__)


class DoubleSlider(QtWidgets.QSlider):
    # The slider class manages value scaling between int and float
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scale_factor = config.get_float_scale_factor()
        self._interval = config.get_default_interval()

    def setInterval(self, interval):
        """Set the interval (step size)"""
        self._interval = interval
        # For floats, we need to scale the interval
        scaled_step = int(interval * self._scale_factor) if isinstance(interval, float) else interval
        super().setSingleStep(scaled_step)
        
    def interval(self):
        """Get the interval (step size)"""
        return self._interval

    def get_interval_fmt_str(self):
        """Return formatting string based on interval precision"""
        str_interval = str(self._interval)
        if '.' in str_interval:
            decimal_places = len(str_interval.split('.')[-1])
            return f'.{decimal_places}f'
        return '.0f'
    
    def _show_tooltip(self, text, duration=None, y_offset=None):
        """Show tooltip with the current value at the slider handle position"""
        if duration is None:
            duration = config.get_tooltip_duration()
        if y_offset is None:
            y_offset = config.get_tooltip_y_offset()
            
        handle_pos = self.style().subControlRect(
            QStyle.CC_Slider, 
            self.style().CC_Slider, 
            QStyle.SC_SliderHandle, 
            self
        )
        global_pos = self.mapToGlobal(handle_pos.center())
        QtWidgets.QToolTip.showText(
            QtCore.QPoint(global_pos.x(), global_pos.y() + y_offset),
            str(text),
            self,
            QtCore.QRect(),
            duration
        )


class IntQSlider(DoubleSlider):
    """A QSlider that will emit integers"""

    value_changed = QtCore.Signal(int)

    @QtCore.Slot(int)
    def _handle_changed(self, val):
        """Re-Emit the underlying value and not the index"""
        real_val = int(self.value())
        self.setToolTip(str(real_val))
        self._show_tooltip(real_val)
        self.value_changed.emit(real_val)


class FloatQSlider(DoubleSlider):
    """A QSlider that will emit Floats"""

    value_changed = QtCore.Signal(float)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scale_factor = config.get_float_scale_factor()

    def value(self):
        """Return the float value"""
        return super().value() / self._scale_factor

    def setValue(self, value):
        """Set the float value by scaling it to an integer"""
        super().setValue(int(value * self._scale_factor))

    def setMinimum(self, value):
        """Set the minimum float value by scaling it to an integer"""
        # Convert numpy.float64 to Python float if needed
        value = float(value)
        super().setMinimum(int(value * self._scale_factor))

    def setMaximum(self, value):
        """Set the maximum float value by scaling it to an integer"""
        # Convert numpy.float64 to Python float if needed
        value = float(value)
        super().setMaximum(int(value * self._scale_factor))

    def minimum(self):
        """Return the minimum as a float"""
        return super().minimum() / self._scale_factor

    def maximum(self):
        """Return the maximum as a float"""
        return super().maximum() / self._scale_factor

    @QtCore.Slot(int)
    def _handle_changed(self, val):
        """Re-Emit the underlying value and not the index"""
        real_val = float(self.value())
        fmt = self.get_interval_fmt_str()
        self.setToolTip(f"{real_val:{fmt}}")
        self._show_tooltip(f"{real_val:{fmt}}")
        self.value_changed.emit(real_val)


class EditableQLabel(QtWidgets.QStackedWidget):
    """A QLabel that be edited by doubleClicking; emits valueChanged"""

    valueChanged = QtCore.Signal(str)

    def __init__(self, txt, alignment, validator=None, width=None, parent=None):
        """
        Initializes the custom widget with a label and a line edit.

        Args:
            txt (str): The text to display on the label.
            alignment (Qt.Alignment): The alignment for the label and line edit.
            validator (QValidator, optional): The validator to set on the line edit. Defaults to None.
            width (int, optional): The fixed width of the widget. Defaults to config value.
            parent (QtWidgets.QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent=parent)
        if width is None:
            width = config.get_editable_label_width()
        self.setFixedWidth(width)
        self.setFixedHeight(config.get_editable_label_height())
        self.edit = QtWidgets.QLineEdit()
        self.edit.setAlignment(alignment)
        if validator:
            self.edit.setValidator(validator)
        self.label = QtWidgets.QLabel(str(txt), alignment=alignment)
        self.label.installEventFilter(self)
        self.edit.installEventFilter(self)
        self.addWidget(self.label)
        self.addWidget(self.edit)

    def set_validator(self, validator):
        """
        Set a validator for the edit widget.

        Parameters:
        validator (QValidator): The validator to be set for the edit widget.
        """
        self.edit.setValidator(validator)

    def setText(self, text):
        """
        Set the text of the label widget.

        Parameters:
        text (str): The text to be set on the label.
        """
        self.label.setText(text)

    def set_width(self, width):
        """
        Set the fixed width of the widget.

        Parameters:
        width (int): The width to set for the widget.
        """
        self.setFixedWidth(width)

    def eventFilter(self, obj: QtWidgets.QWidget, event: QtCore.QEvent):
        """
        Filters events for the specified objects.

        This method intercepts events for the given objects (label and edit) and 
        handles them accordingly. If the event is associated with the label, it 
        calls the `_handle_label` method. If the event is associated with the edit, 
        it calls the `_handle_edit` method. For all other objects, it passes the 
        event to the superclass's eventFilter method.

        Args:
            obj (QtWidgets.QWidget): The widget that received the event.
            event (QtCore.QEvent): The event that occurred.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        # Safety check to prevent crashes
        if obj is None or not isinstance(obj, QtWidgets.QWidget) or event is None:
            return False
            
        if obj == self.label:
            if self._handle_label(event):
                return True
        elif obj == self.edit:
            if self._handle_edit(event):
                return True

        return super().eventFilter(obj, event)

    def _handle_label(self, event: QtCore.QEvent):
        """
        Handles the label double-click event to switch to an editable text field.

        Args:
            event (QtCore.QEvent): The event object containing information about the event.

        If the event is a double-click on the label, this method will:
        - Set the text of the editable field to the current label text.
        - Switch the current widget to the editable field.
        - Select all text in the editable field.
        - Set focus to the editable field.
        
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
            self.edit.setText(self.label.text())
            self.setCurrentWidget(self.edit)
            self.edit.selectAll()
            self.edit.setFocus()
            return True
        return False

    def _handle_edit(self, event: QtCore.QEvent):
        """
        Handles edit events for the widget.

        This method processes key press and focus out events to manage the 
        transition between the edit and label widgets. It updates the label 
        text based on the edit input and emits a valueChanged signal when 
        the Enter key is pressed. It also handles the Escape key to revert 
        to the label widget and manages focus out events to switch back to 
        the label widget.

        Args:
            event (QtCore.QEvent): The event to handle.
            
        Returns:
            bool: True if the event was handled, False otherwise.
        """
        if event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                if not self.edit.hasAcceptableInput():
                    self.setCurrentWidget(self.label)
                    return True
                self.label.setText(self.edit.text())
                self.setCurrentWidget(self.label)
                self.valueChanged.emit(self.label.text())
                return True
            if key == QtCore.Qt.Key.Key_Escape:
                self.setCurrentWidget(self.label)
                return True
            return False
        elif event.type() == QtCore.QEvent.FocusOut:
            self.setCurrentWidget(self.label)
            return True
        return False


class SliderContainer(QtWidgets.QWidget):
    def __init__(self, slider, editable_range=True, parent=None, show_editable_value=None):
        super().__init__(parent=parent)
        self.slider = slider
        self.editable_range = editable_range
        
        # Use config value if not explicitly provided
        if show_editable_value is None:
            show_editable_value = config.should_show_editable_value()
        self.show_editable_value = show_editable_value
        
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top row with min/max labels and value display
        top_layout = QtWidgets.QHBoxLayout()
        
        self.min_label = QtWidgets.QLabel(str(slider.minimum()))
        if self.editable_range:
            self.min_label.mouseDoubleClickEvent = self.edit_min_value
        
        self.max_label = QtWidgets.QLabel(str(slider.maximum()))
        if self.editable_range:
            self.max_label.mouseDoubleClickEvent = self.edit_max_value
        
        # Create spin box for numeric input
        self.value_spinbox = self._create_spin_box(slider)
        
        top_layout.addWidget(self.min_label)
        top_layout.addStretch()
        top_layout.addWidget(self.value_spinbox)
        top_layout.addStretch()
        top_layout.addWidget(self.max_label)
        
        # Add slider
        layout.addLayout(top_layout)
        layout.addWidget(slider)
        
        self.setLayout(layout)
        
        # Connect signals
        self.slider.valueChanged.connect(self.update_spinbox_from_slider)
        self.value_spinbox.valueChanged.connect(self.update_slider_from_spinbox)
    
    def _create_spin_box(self, slider):
        """Create appropriate spin box based on slider type"""
        if isinstance(slider, IntQSlider):
            spinbox = QtWidgets.QSpinBox()
        else:  # FloatQSlider
            spinbox = QtWidgets.QDoubleSpinBox()
            # Set decimals based on slider's interval property
            interval = slider.interval()
            if interval < 1:
                decimal_places = len(str(interval).split('.')[-1])
                spinbox.setDecimals(decimal_places)
        
        # Apply configuration
        spinbox.setMinimumWidth(config.get_spinbox_min_width())
        spinbox.setAlignment(config.get_spinbox_alignment())
        
        spinbox.setMinimum(slider.minimum())
        spinbox.setMaximum(slider.maximum())
        spinbox.setSingleStep(slider.interval())
        spinbox.setValue(slider.value())
        return spinbox
    
    def update_spinbox_from_slider(self, value):
        """Update spinbox when slider changes"""
        self.value_spinbox.blockSignals(True)
        if isinstance(self.slider, FloatQSlider):
            self.value_spinbox.setValue(value / self.slider._scale_factor)
        else:
            self.value_spinbox.setValue(value)
        self.value_spinbox.blockSignals(False)
    
    def update_slider_from_spinbox(self, value):
        """Update slider when spinbox changes"""
        self.slider.blockSignals(True)
        if isinstance(self.slider, FloatQSlider):
            self.slider.setValue(value * self.slider._scale_factor)
        else:
            self.slider.setValue(value)
        self.slider.blockSignals(False)
        # Forward the value changed signal
        self.slider.valueChanged.emit(value)
    
    def edit_min_value(self, event):
        """Handle double-click on min label to edit minimum value"""
        current_min = self.slider.minimum()
        current_max = self.slider.maximum()
        
        # Get new value from user
        new_value, ok = QtWidgets.QInputDialog.getDouble(
            self,
            "Edit Minimum Value",
            "Enter new minimum value:",
            current_min,
            float('-inf'),  # No minimum limit
            current_max,    # Maximum can't be higher than current maximum
            config.get_decimal_places()  # Decimal places from config
        )
        
        if ok:
            # Update the slider
            self.slider.setMinimum(new_value)
            self.min_label.setText(str(new_value))
            
            # Also update the spinbox
            self.value_spinbox.setMinimum(new_value)
            
            # Ensure current value isn't below new minimum
            if self.slider.value() < new_value:
                self.slider.setValue(new_value)
    
    def edit_max_value(self, event):
        """Handle double-click on max label to edit maximum value"""
        current_min = self.slider.minimum()
        current_max = self.slider.maximum()
        
        # Get new value from user
        new_value, ok = QtWidgets.QInputDialog.getDouble(
            self,
            "Edit Maximum Value",
            "Enter new maximum value:",
            current_max,
            current_min,  # Minimum can't be lower than current minimum
            float('inf'), # No maximum limit
            config.get_decimal_places()  # Decimal places from config
        )
        
        if ok:
            # Update the slider
            self.slider.setMaximum(new_value)
            self.max_label.setText(str(new_value))
            
            # Also update the spinbox
            self.value_spinbox.setMaximum(new_value)
            
            # Ensure current value isn't above new maximum
            if self.slider.value() > new_value:
                self.slider.setValue(new_value)


class SliderPair(SliderContainer):
    """Shows min/max values and provides two text input fields for setting values"""
    
    # Add missing signals
    topChanged = QtCore.Signal(int)
    botChanged = QtCore.Signal(int)
    
    def __init__(self, top_slider, bot_slider, editable_range=True, parent=None):
        super().__init__(
            slider=top_slider,
            editable_range=editable_range,
            parent=parent,
            show_editable_value=True,
        )
        
        # Create horizontal layout for both values
        value_layout = QtWidgets.QHBoxLayout()
        
        # Store bot_slider but don't show it
        self.bot_slider = bot_slider
        self.bot_slider.setParent(self)
        self.bot_slider.hide()
        
        # Add second value input
        validator = self._get_validator(self.bot_slider, 
                                       self.bot_slider.minimum(), 
                                       self.bot_slider.maximum())
        self.bot_slider_text = EditableQLabel(
            str(self.bot_slider.value()),
            width=config.get_slider_pair_value_width(),  # Use config value
            validator=validator,
            alignment=QtCore.Qt.AlignLeft,
        )
        
        # Labels for the two values
        top_label = QtWidgets.QLabel("Value 1:")
        bot_label = QtWidgets.QLabel("Value 2:")
        
        # Add to layout
        value_layout.addWidget(top_label)
        value_layout.addWidget(self.value_spinbox)  # Use spinbox instead of slider_text
        value_layout.addWidget(bot_label)
        value_layout.addWidget(self.bot_slider_text)
        
        # Add this layout below the range display
        self.layout().addLayout(value_layout)
        
        # Connect signals
        top_slider.valueChanged.connect(self._emit_top_changed)
        bot_slider.valueChanged.connect(self._emit_bot_changed)
        self.bot_slider_text.valueChanged.connect(self._handle_bot_text_input)
        self.bot_slider.valueChanged.connect(self._handle_bot_slider_changed)
    
    def _get_validator(self, slider, min_value, max_value):
        """Create appropriate validator based on slider type"""
        if isinstance(slider, IntQSlider):
            return QtGui.QIntValidator(min_value, max_value)
        else:  # FloatQSlider
            return QtGui.QDoubleValidator(min_value, max_value, slider.get_interval_fmt_str().count('f'))
    
    @QtCore.Slot(int)
    def _emit_top_changed(self, value):
        """Emit the top slider changed signal"""
        self.topChanged.emit(value)
    
    @QtCore.Slot(int)
    def _emit_bot_changed(self, value):
        """Emit the bottom slider changed signal"""
        self.botChanged.emit(value)
    
    @QtCore.Slot(str)
    def _handle_bot_text_input(self, val):
        """Set bot slider to specified value"""
        if isinstance(self.bot_slider, FloatQSlider):
            self.bot_slider.setValue(float(val))
        else:
            self.bot_slider.setValue(int(val))
    
    @QtCore.Slot(float)
    @QtCore.Slot(int)
    def _handle_bot_slider_changed(self, _):
        """Update bot slider text"""
        val = self.bot_slider.value()
        if isinstance(val, float):
            fmt = self.bot_slider.get_interval_fmt_str()
            real_val = f"{val:{fmt}}"
        else:
            real_val = str(val)
        self.bot_slider_text.setText(real_val)
