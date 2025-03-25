"""
OpenCV Documentation Viewer Module

This module provides a Qt-based documentation viewer for OpenCV documentation templates.
It manages rendering, displaying, and refreshing documentation from HTML templates.
"""
import os
from typing import Optional

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

from docs import doc_writer
from utils.config_manager import ConfigManager

config: ConfigManager = ConfigManager()

# Ensure the rendered_docs folder exists
try:
    os.makedirs(doc_writer.RENDERED_DIR, exist_ok=True)
except OSError as e:
    print(f"Error creating rendered_docs directory: {e}")


class MyWebView(QWebEngineView):
    """
    A custom QWebEngineView that overrides the context menu event.

    Methods
    -------
    contextMenuEvent(event)
        Handles the context menu event by reloading the parent widget if it has a 'reload' method.
    """
    def contextMenuEvent(self, event):
        # Only reload on context menu if configured to do so
        if config.should_reload_template_on_context_menu():
            if hasattr(self.parent(), 'reload'):
                self.parent().reload()


class DocWindow(QMainWindow):
    """
    A class to represent the main window of the OpenCV DocViewer application.
    Attributes:
        _template_name (str): The name of the template to be loaded.
    Methods:
        __init__(template_name):
            Initializes the DocWindow with the given template name.
        _load_webview(template_name):
            Loads the specified template into a WebView widget.
        reload():
            Reloads the current view.
        _setup_window_dims():
            Sets up the default window dimensions.
        _add_statusbar(fname):
        _add_menus():
    """
    def __init__(self, template_name):
        """
        Initializes the DocViewer window with the specified template.

        Args:
            template_name (str): The name of the template to be used for rendering the document.

        Sets up the window title, dimensions, status bar, menus, and loads the web view with the given template.
        """
        super().__init__()
        self._setup_window_dims()
        self._add_statusbar(template_name)
        self._add_menus()
        self._load_webview(template_name)
        self._template_name = template_name
        QTimer.singleShot(0, self._initialize_docs)
        self._load_webview(template_name)
    def _initialize_docs(self):
        """
        Initializes the rendered docs by calling the doc_writer method.
        """
        doc_writer._create_rendered_docs()

    def _load_webview(self, template_name):
        """
        Loads a web view with the specified template.

        This method initializes a MyWebView instance, checks if the rendered template
        needs to be updated based on its modification time, and then loads the rendered
        template into the web view.

        Args:
            template_name (str): The name of the template to be loaded.

        """
        view = MyWebView(self)
        template_path = doc_writer.TEMPLATE_DIR.joinpath(template_name)
        rendered_path = doc_writer.RENDERED_DIR.joinpath(template_name)
        if not rendered_path.exists() or template_path.stat().st_mtime > rendered_path.stat().st_mtime:
            doc_writer.render_local_doc(doc_writer.RENDERED_DIR, template_name)
        doc_name = doc_writer.RENDERED_DIR.joinpath(template_name)
        url = QUrl.fromLocalFile(str(doc_name))
        # Load the document in the web view
        view.load(url)
        self.setCentralWidget(view)
        view.show()

    def reload(self):
        """
        Reloads the document template if it has been modified.

        This method checks if the rendered document needs to be updated by comparing
        the modification times of the template and the rendered document. If the
        template has been modified more recently than the rendered document, it
        triggers a reload.

        Prints:
            "RELOAD" to indicate the reload process has started.
        """
        print("RELOAD")
        template_path = doc_writer.TEMPLATE_DIR.joinpath(self._template_name)
        rendered_path = doc_writer.RENDERED_DIR.joinpath(self._template_name)
        if not rendered_path.exists() or template_path.stat().st_mtime > rendered_path.stat().st_mtime:
            doc_writer.render_local_doc(doc_writer.RENDERED_DIR, self._template_name)
        self._load_webview(self._template_name)

    def _setup_window_dims(self):
        """
        Sets up the default window dimensions based on configuration or screen size.
        """
        width = config.get('Window', 'doc_window_width', 800, int)
        height = config.get('Window', 'doc_window_height', 600, int)
        self.resize(width, height)

    def resizeEvent(self, event):
        """
        Handles the resize event for the widget.

        This method is called whenever the widget is resized. It ensures that
        the parent class's resizeEvent method is also called to handle any
        additional resize logic.

        Args:
            event (QResizeEvent): The resize event object containing information
                                  about the resize event.
        """
        super().resizeEvent(event)

    def _add_statusbar(self, fname):
        """
        Adds a status bar to the application window and displays a message.

        Args:
            fname (str): The message to be displayed on the status bar.
        """
        self.status = self.statusBar()
        self.status.showMessage(fname)

    def _add_menus(self):
        """
        Adds menus to the menu bar of the application.
        This method creates a menu bar with a "File" menu that contains the following actions:
        """
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.reload)
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction(refresh_action)
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
