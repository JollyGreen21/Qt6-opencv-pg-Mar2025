import logging
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
import os

from docs.doc_writer import render_local_doc
from doc_viewer import DocWindow
from docs import doc_writer  # Update this import

# Ensure doc_writer.RENDERED_DIR is defined
if not hasattr(doc_writer, 'RENDERED_DIR'):
    doc_writer.RENDERED_DIR = 'path_to_rendered_docs'  # Update this path as needed

log = logging.getLogger(__name__)

class TransformDocButton(QtWidgets.QPushButton):
    """A button that opens documentation for a transform"""
    
    def __init__(self, transform_class, parent=None):
        super().__init__("?", parent)
        self.transform_class = transform_class
        self.setFixedSize(20, 20)
        self.setToolTip(f"View documentation for {transform_class.__name__}")
        self.clicked.connect(self.show_documentation)
        
    def show_documentation(self):
        """Open documentation window for this transform"""
        try:
            # Define the doc filename
            doc_filename = f"{self.transform_class.__name__}.html"
            
            # Ensure the doc file exists in rendered_docs
            doc_path = os.path.join(doc_writer.RENDERED_DIR, doc_filename)
            if not os.path.exists(doc_path):
                doc_writer.render_local_doc(self.transform_class)
            
            # Open the documentation window
            self.doc_window = DocWindow(doc_path, parent=self)
            self.doc_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.doc_window.show()
            
        except (FileNotFoundError, IOError) as e:
            log.error(f"Failed to show documentation: {e}")
            QtWidgets.QMessageBox.warning(
                self, 
                "Documentation Error",
                f"Could not display documentation: {str(e)}"
            )
