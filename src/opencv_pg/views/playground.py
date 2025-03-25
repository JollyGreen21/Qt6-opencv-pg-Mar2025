import logging
import os
try:
    from models.transforms import BaseTransform
except ImportError as e:
    basic_transforms = None
    print(f"Warning: Failed to import basic_transforms: {e}")

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView

from docs.doc_writer import RENDERED_DIR
from models.pipeline import Pipeline
from models.transform_windows import get_transform_window

from .pipeline_window import PipeWindow
from .widgets.transform_list import TransformList

log = logging.getLogger(__name__)


class Playground(QtWidgets.QSplitter):
    """
    Playground is a custom QtWidgets.QSplitter that provides a graphical interface for 
    managing image transformations and displaying related documentation.

        img_path (str): Path to the image file.
        show_info_widgets (bool): Flag to determine if the info widgets should be shown.
        docview (QWebEngineView): A web engine view for displaying documentation.
        added_pipes (dict): Dictionary to keep track of added pipelines.

    Methods:
        _build_layout(): Builds the main layout of the playground view.
        clear_pipeline_stack(): Clears the pipeline stack and resets the added pipes dictionary.
        _reload_pipeline(current=None, previous=None): Creates or loads the selected transform into the pipe window.
        _handle_changed(current, previous): Reloads documentation for the selected transform.
        display_image_in_new_window(img): Displays the loaded image in a new independent window.
        load_image(img_path): Loads a new image and updates the pipeline.
        resizeEvent(event): Handles window resizing.'
        """
    def __init__(
        self, img_path, no_docs, disable_info_widgets, parent=None, *args, **kwargs
    ):
        super().__init__(parent=parent, *args, **kwargs)
        self.img_path = str(img_path)
        self.show_docs = not no_docs
        self.show_info_widgets = not disable_info_widgets
        self.docview = None
        self.pipe_stack = None
        self.added_pipes = {}
        self.transform_list = None

        self.setOrientation(Qt.Orientation.Horizontal)
        self._build_layout()
        # TODO: Distribution based on screen size
        self.setSizes([int(0.1 * 800), int(0.5 * 800), int(0.4 * 800)])

    def _build_layout(self):
        """
        Build the main layout of the playground view.

        This method sets up the layout by adding a TransformList widget, 
        connecting change handlers, and optionally adding a document viewer 
        and a pipe window.

        Attributes:
            show_docs (bool): Flag to determine if the document viewer should be shown.

        Widgets:
            tlist (TransformList): A list widget for transformations with a minimum 
                width of 150 and a maximum width of 200.
            docview (QWebEngineView): A web engine view for displaying documentation 
                (only if show_docs is True).
            pipe_stack (QtWidgets.QStackedWidget): A stacked widget for the pipeline window.

        Connections:
            tlist.builtin_list.selectionModel().currentChanged: Connects to 
                _handle_changed if show_docs is True, and always connects to 
                _reload_pipeline.
        """
        """Build the main layout"""
        tlist = TransformList()
        
        # Calculate the width of the longest text in the transforms list
        max_text_width = self._calculate_max_text_width(tlist)
        
        # Set the width of the TransformList based on the longest text
        tlist.setMinimumWidth(max_text_width + 40)  # Add some padding
        tlist.setMaximumWidth(max_text_width + 40)  # Add some padding
        self.addWidget(tlist)
        self.transform_list = tlist

        # Connect change handlers for the transform list
        if self.show_docs:
            tlist.builtin_list.selectionModel().currentChanged.connect(
                self._handle_changed
            )
        tlist.builtin_list.selectionModel().currentChanged.connect(
            self._reload_pipeline
        )

        # Document Viewer
        if self.show_docs:
            self.docview = QWebEngineView(parent=self)
            self.docview.setAttribute(
                QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, False
            )
            self.addWidget(self.docview)
            # NOTE: No idea why, but we get random segfaults if we don't first set/load
            # some kind of html before the signal handler takes over ... :shrug:
            self.docview.setHtml("")

        # PipeWindow
        self.pipe_stack = QtWidgets.QStackedWidget(parent=self)
        self.addWidget(self.pipe_stack)

    def _calculate_max_text_width(self, tlist):
        """
        Calculate the width of the longest text in the transforms list.

        Args:
            tlist (TransformList): The TransformList widget.

        Returns:
            int: The width of the longest text in pixels.
        """
        max_width = 0
        font_metrics = QtGui.QFontMetrics(tlist.font())
        
        # Iterate through the items in the builtin list
        for i in range(tlist.builtin_list.model().rowCount(QtCore.QModelIndex())):
            index = tlist.builtin_list.model().index(i, 0)
            text = tlist.builtin_list.model().data(index)
            text_width = font_metrics.horizontalAdvance(text)
            if text_width > max_width:
                max_width = text_width
        
        return max_width

    def clear_pipeline_stack(self):
        """
        Clears all widgets from the pipeline stack and resets the added pipes dictionary.
        This method iterates through the pipeline stack, removing and deleting each widget
        until the stack is empty. It then resets the `added_pipes` dictionary to an empty state.
        """
        while self.pipe_stack.count() > 0:
            widget = self.pipe_stack.widget(0)
            self.pipe_stack.removeWidget(widget)
            if widget:
                widget.deleteLater()
        
        self.added_pipes = {}

    @Slot(QModelIndex, QModelIndex)
    def _reload_pipeline(self, current=None, previous=None):
        """
        Reloads the image processing pipeline based on the current or previous selection.
        This method attempts to reload the image processing pipeline using the current selection
        from the sender or the transform list. If no current selection is provided, it defaults
        to the first available transform. If no image path is specified, the method logs a warning
        and returns early.
        Args:
            current (Optional[QModelIndex]): The current index of the selected transform. Defaults to None.
            previous (Optional[QModelIndex]): The previous index of the selected transform. Defaults to None.
        Raises:
            Exception: If there is an error getting the current index from the sender or creating the default transform.
        """
        if not self.img_path:
            log.warning("Cannot reload pipeline: No image path specified")
            return

        current = self._get_current_index(current)
        if current is None:
            self._load_default_transform()
            return
        if current is not None:
            self._load_transform(current)
        else:
            log.error("Failed to get a valid current index for the transform.")
        self._load_transform(current)

    def _get_current_index(self, current):
        if current is not None:
            return current
        transform_list = self.transform_list
        try:
            if transform_list is not None and hasattr(transform_list, 'builtin_list'):
                current = transform_list.builtin_list.currentIndex()
                if not current.isValid():
                    transform_list.builtin_list.setCurrentIndex(transform_list.builtin_list.model().index(0, 0))
                    current = transform_list.builtin_list.currentIndex()
                return current
        except Exception as e:
            log.error(f"Error getting current index from sender: {e}")
            return None

        return None

    def _load_default_transform(self):
        try:
            from models.transforms import BaseTransform
            default_transform = basic_transforms.GrayScale
            self._create_and_add_pipe_window(default_transform)
        except ImportError:
            log.error("Module transforms.core not found. Please ensure it is installed and accessible.")
        except Exception as e:
            log.error(f"Error creating default transform: {e}")

    def _load_transform(self, current):
        try:
            model = current.model()
            transform = model.items[current.row()]
            tname = transform.__name__

            if self.pipe_stack.currentIndex() == -1 or tname not in self.added_pipes:
                self._create_and_add_pipe_window(transform)
            else:
                self.pipe_stack.setCurrentIndex(self.added_pipes[tname])
        except Exception as e:
            log.error(f"Error in _reload_pipeline: {e}")

    def _create_and_add_pipe_window(self, transform):
        window = get_transform_window(transform, self.img_path)
        pipe = Pipeline(window)
        pipe_win = PipeWindow(window, parent=self, show_info_widget=self.show_info_widgets)
        img, _ = pipe.run_pipeline()
        pipe_win.update_image(img, pipe_win.viewer)
        self.pipe_stack.addWidget(pipe_win)
        self.added_pipes[transform.__name__] = self.pipe_stack.count() - 1
        self.pipe_stack.setCurrentIndex(self.added_pipes[transform.__name__])

    @Slot(QModelIndex, QModelIndex)
    def _handle_changed(self, current, previous):
        model = current.model()
        transform = model.items[current.row()]
        doc_fname = RENDERED_DIR.joinpath(transform.get_doc_filename())
        url = QUrl.fromLocalFile(str(doc_fname))
        self.docview.load(url)

    def display_image_in_new_window(self, img):
        new_window = QtWidgets.QWidget()
        new_window.setWindowTitle("Loaded Image")
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap.fromImage(img)
        label.setPixmap(pixmap)
        layout.addWidget(label)
        new_window.setLayout(layout)
        new_window.show()

    def load_image(self, img_path):
        if img_path and os.path.exists(img_path):
            try:
                self.img_path = img_path
                self.clear_pipeline_stack()
                self._reload_pipeline()
                if hasattr(self.parent(), 'status_bar'):
                    self.parent().status_bar.showMessage(f"Loaded image: {img_path}")
                
            except Exception as e:
                log.error(f"Error loading image: {e}")
                if hasattr(self.parent(), 'status_bar'):
                    self.parent().status_bar.showMessage(f"Error loading image: {str(e)}")
        else:
            log.error(f"Image not found: {img_path}")
            if hasattr(self.parent(), 'status_bar'):
                self.parent().status_bar.showMessage(f"Image not found: {img_path}")

    def resizeEvent(self, event):
        """Handle window resizing"""
        self.setSizes([int(0.1 * self.width()), int(0.5 * self.width()), int(0.4 * self.width())])
        super().resizeEvent(event)
