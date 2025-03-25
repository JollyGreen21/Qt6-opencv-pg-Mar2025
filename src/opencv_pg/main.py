import os
from PySide6.QtGui import QGuiApplication, QKeySequence, QAction  # GUI related import
from PySide6.QtWidgets import QMainWindow, QApplication, QSplitter, QWidget, QFileDialog  # GUI related import
from PySide6.QtCore import QTimer, __version__ as PYSIDE_VERSION_STR  # GUI related import
from PySide6 import QtCore  # GUI related import
import sys

try:
    from views.playground import Playground
    from utils.config_manager import config
    assert hasattr(Playground, '__init__'), "Playground class not found in playground module"
except (ImportError, AssertionError) as e:
    raise ImportError(f"Failed to import Playground class: {e}")

# Print the Qt version using PySide6
print(f"Using PySide6 version: {PYSIDE_VERSION_STR}")

def is_valid_image(file_path):
    return config.is_valid_image(file_path)

def open_image_file_dialog(parent=None):
    """
    Opens a file dialog to select an image file.

    Args:
        parent (QWidget): The parent widget for the file dialog.  # GUI related comment

    Returns:
        str: The selected file path.
    """
    default_dir = config.get_default_image_dir()
    file_path, _ = QFileDialog.getOpenFileName(  # GUI related code
        parent,
        "Open Image",
        default_dir,
        "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
    )
    if file_path:
        # Save the directory for next time
        config.set_default_image_dir(os.path.dirname(file_path))
    return file_path

def handle_image_loading(playground_widget, file_path, status_bar):
    if not file_path:
        status_bar.showMessage("No file selected")  # GUI related code
        return
    if not is_valid_image(file_path):
        status_bar.showMessage(f"Error: Invalid or non-existent image file - {file_path}")  # GUI related code
        return

    if not hasattr(playground_widget, 'load_image'):
        status_bar.showMessage("Reloading Playground widget")  # GUI related code
        new_widget = Playground("", False, False)
        central_splitter = playground_widget.parent().centralWidget()  # GUI related code
        central_splitter.replaceWidget(0, new_widget)  # GUI related code
        playground_widget = new_widget

    try:
        if hasattr(playground_widget, 'load_image'):
            playground_widget.load_image(file_path)
            playground_widget.update()  # GUI related code
            status_bar.showMessage(f"Loaded image: {os.path.basename(file_path)}")  # GUI related code
        else:
            status_bar.showMessage("Error: Cannot load image (invalid widget)")  # GUI related code
    except AttributeError as e:
        status_bar.showMessage(f"Error loading image: {str(e)} - Application will continue")  # GUI related code
    except FileNotFoundError as e:
        status_bar.showMessage(f"Error: File not found - {str(e)}")  # GUI related code
    except Exception as e:
        status_bar.showMessage(f"Unexpected error loading image: {str(e)} - Application will continue")  # GUI related code


class MainWindow(QMainWindow):  # GUI related class
    def __init__(self, img_path, no_docs, disable_info_widgets):
        super().__init__()
        # TODO: Still get the t.pointer.dispatch: skipping QEventPoint warning
        # when clicking on another window
        # TODO: Investigate the t.pointer.dispatch: skipping QEventPoint warning.
        # This warning occurs when clicking on another window, possibly due to touch event handling.
        # Potential solutions:
        # 1. Ensure that touch events are properly managed or disabled if not needed.
        # 2. Check if there are any conflicting event filters or handlers.
        # 3. Update the Qt version to see if the issue is resolved in a newer release.
        
        # Disable touch event synthesis to potentially fix QEventPoint warnings
        QGuiApplication.setAttribute(QtCore.Qt.AA_SynthesizeMouseForUnhandledTouchEvents, False)  # GUI related code
        QGuiApplication.setAttribute(QtCore.Qt.AA_SynthesizeTouchForUnhandledMouseEvents, False)  # GUI related code
        
        # Disable touch events globally if not needed
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, False)  # GUI related code
        
        # Override command line flags with config if not explicitly set
        if no_docs is None:
            no_docs = not config.get('UI', 'show_docs', True, bool)
        if disable_info_widgets is None:
            disable_info_widgets = not config.get('UI', 'show_info_widgets', True, bool)
        
        self._setup_window_size(config.get('Window', 'main_window_size_factor', 0.5, float))
        self._add_statusbar()  # GUI related code
        self._add_menus()  # GUI related code
        
        # Store flags for later use
        self.no_docs = no_docs
        self.disable_info_widgets = disable_info_widgets
        
        # Set window title from configuration
        self.setWindowTitle(config.get_window_title())
        
        # Create a QSplitter to allow resizing between playground and side widget
        self.playground_widget = Playground(img_path, no_docs, disable_info_widgets)  # GUI related code
        self.side_widget = QWidget()  # New side area (customize as needed)  # GUI related code
        splitter = QSplitter(QtCore.Qt.Horizontal)  # GUI related code
        splitter.addWidget(self.playground_widget)  # GUI related code
        
        # Add side widget if configured to do so
        if config.should_show_side_widget():
            splitter.addWidget(self.side_widget)  # GUI related code
            
        ratio = config.get('Window', 'playground_splitter_ratio', 0.75, float)
        splitter.setSizes([int(self.width() * ratio), int(self.width() * (1-ratio))])
        self.setCentralWidget(splitter)  # GUI related code
        
        # Store splitter for later reference in resize events
        self.splitter = splitter
        
        # Add a QTimer to repaint the playground_widget every second
        self.timer = QTimer(self)  # GUI related code
        self.timer.timeout.connect(self._repaint_playground)  # GUI related code
        self.timer.start(config.get_timer_interval())  # Use configured interval
        
        self.installEventFilter(self)  # Install event filter  # GUI related code
        self.show()  # Make sure window is visible  # GUI related code
        self.setAcceptDrops(True)  # Enable drag and drop  # GUI related code

    def _setup_window_size(self, fraction):
        screen = QGuiApplication.primaryScreen()  # GUI related code
        geometry = screen.geometry()  # GUI related code
        width = int(geometry.width() * fraction)  # GUI related code
        height = int(geometry.height() * fraction)  # GUI related code
        self.resize(width, height)  # GUI related code

    def _add_statusbar(self):
        self.status_bar = self.statusBar()  # GUI related code
        self.status_bar.showMessage(config.get_welcome_message())  # GUI related code

    def _add_menus(self):
        self.menu_bar = self.menuBar()  # GUI related code
        self.menu_bar.setNativeMenuBar(False)  # GUI related code
        self.file_menu = self.menu_bar.addMenu("File")  # GUI related code

        # Add Open action
        open_action = QAction("Open", self)  # GUI related code
        open_action.setShortcut(QKeySequence.Open)  # Usually Ctrl+O  # GUI related code
        open_action.triggered.connect(self._open_image)  # GUI related code
        self.file_menu.addAction(open_action)  # GUI related code
        
        # Add a separator
        self.file_menu.addSeparator()  # GUI related code
        
        # Add Edit Config action
        config_action = QAction("Edit Configuration", self)
        config_action.triggered.connect(self._edit_config)
        self.file_menu.addAction(config_action)
        
        # Add another separator
        self.file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)  # GUI related code
        exit_action.setShortcut(QKeySequence.Quit)  # GUI related code
        exit_action.triggered.connect(self.close)  # GUI related code
        
        self.file_menu.addAction(exit_action)  # GUI related code
    
    def _edit_config(self):
        """Open the configuration file in the default text editor"""
        if config.open_config_file():
            self.status_bar.showMessage(f"Opened configuration file: {config.config_path}")
        else:
            self.status_bar.showMessage(f"Error opening configuration file")

    def _open_image(self):
        file_path = open_image_file_dialog(self)  # Use the function from utils.py  # GUI related code
        if file_path:  # Check if a file was selected
            handle_image_loading(self.playground_widget, file_path, self.status_bar)  # Use the function from utils.py  # GUI related code

    def _repaint_playground(self):
        self.playground_widget.repaint()  # GUI related code

    def dragEnterEvent(self, event):
        # Accept if the dragged data has URLs.
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # GUI related code
        else:
            event.ignore()  # GUI related code
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()  # GUI related code
        if urls:
            file_path = urls[0].toLocalFile()  # GUI related code
            handle_image_loading(self.playground_widget, file_path, self.status_bar)  # Use the function from utils.py  # GUI related code
        event.acceptProposedAction()  # GUI related code

    def eventFilter(self, obj, event):
        # Safety check to prevent crashes with null objects or events
        if obj is None or event is None:
            return False
            
        # Use configuration values for touch event handling
        if event.type() == QtCore.QEvent.TouchBegin and config.should_block_touch_begin():  # GUI related code
            return True  # Block the event from further processing
        elif event.type() == QtCore.QEvent.TouchEnd and config.should_block_touch_end():  # GUI related code
            return True  # Block the event from further processing
        elif event.type() == QtCore.QEvent.TouchUpdate and config.should_block_touch_update():  # GUI related code
            return True  # Block the event from further processing
        elif event.type() == QtCore.QEvent.MouseMove:  # Exclude logging for mouse move events  # GUI related code
            return super().eventFilter(obj, event)
        elif event.type() == QtCore.QEvent.HoverEnter or event.type() == QtCore.QEvent.HoverLeave or event.type() == QtCore.QEvent.HoverMove:  # Exclude logging for hover events  # GUI related code
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        # Complete the resize event handler to properly set splitter sizes
        if hasattr(self, 'splitter'):
            ratio = config.get('Window', 'playground_splitter_ratio', 0.75, float)
            self.splitter.setSizes([int(self.width() * ratio), int(self.width() * (1-ratio))])
        super().resizeEvent(event)

"""
def some_function_with_combobox():
    # Assuming combo_box is an instance of QComboBox
    value = 1  # Example integer value
    combo_box.setCurrentText(str(value))  # Convert integer to string
"""

# Application entry point
def main():
    # Set high DPI attributes before creating QApplication
    if hasattr(QtCore.Qt, 'HighDpiScaleFactorRoundingPolicy') and config.is_high_dpi_scaling_enabled():
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    
    # Use Qt.ApplicationAttribute enum instead of direct access to avoid deprecation warnings
    if hasattr(QtCore.Qt, 'ApplicationAttribute'):
        QGuiApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    else:
        # Fallback for older Qt versions
        QGuiApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)  # GUI related code
    
    img_path = sys.argv[1] if len(sys.argv) > 1 else None
    no_docs = "--no-docs" in sys.argv
    disable_info_widgets = "--disable-info" in sys.argv
    
    window = MainWindow(img_path, no_docs, disable_info_widgets)  # GUI related code
    
    sys.exit(app.exec())  # Remove underscore  # GUI related code

if __name__ == "__main__":
    main()
