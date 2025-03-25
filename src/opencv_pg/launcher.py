import argparse
import logging
from logging import config
from pathlib import Path
from typing import Union, Optional

from PySide6 import QtCore, QtWidgets  # Updated import

from .doc_viewer import DocWindow  # GUI related import
from .main import MainWindow  # GUI related import
from .pipeline_launcher import LOG_FORMAT

def get_file_path(rel_path: Union[str, Path]) -> Path:
    """
    Resolves the absolute path of a file relative to the current file's directory.

    Args:
        rel_path (Union[str, Path]): The relative path to be resolved.

    Returns:
        Path: The absolute path resolved from the relative path.
    """
    current_file_path = Path(__file__)
    relative_path = Path(rel_path)
    return current_file_path.parent.joinpath(relative_path)


def run_playground(args: argparse.Namespace) -> None:
    """Run the playground"""
    img_path = args.image
    if img_path is None:
        pass
    else:
        _validate_image_path(img_path)
        
    app = QtWidgets.QApplication.instance()  # GUI related code
    if app is None:
        app = QtWidgets.QApplication([])  # GUI related code
    main_window = MainWindow(img_path, args.no_docs, args.disable_info_widgets)  # GUI related code
    main_window.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, False)  # GUI related code
    main_window.show()  # GUI related code
    app.exec()  # Updated to use PySide6 style


def docview() -> None:
    """Launch a WebEngine to view docs"""
    parser = argparse.ArgumentParser("OpenCV DocView")
    parser.add_argument(
        "--template",
        type=str,
        required=True,
        help="Template name in docs/source_docs folder, eg, GaussianBlur.html",
    )

    args = parser.parse_args()
    
    app = QtWidgets.QApplication.instance()  # GUI related code
    if app is None:
        app = QtWidgets.QApplication([])  # GUI related code
    doc_window = DocWindow(args.template)  # GUI related code
    doc_window.show()  # GUI related code
    app.exec()  # Updated to use PySide6 style


def _validate_image_path(img_path: Optional[Union[str, Path]]) -> None:
    """Raise FileNotFoundError if img_path doesn't exist"""
    if img_path is not None and not Path(img_path).exists():
        logging.error(f"Image not found: {img_path}")  # Added logging error
        raise FileNotFoundError(img_path)


def main() -> None:
    """
    Application entrypoint.

    This function sets up the argument parser for the OpenCV Playground application,
    parses the command-line arguments, configures logging, validates the image path,
    and runs the playground with the provided arguments.

    Command-line arguments:
        --image: Path to the image to load into the playground (default: None)
        --no-docs: Do not load the doc window (default: False)
        --disable-info-widgets: Disable all info widgets (default: False)
        --log-level: Set the logging level (default: INFO, choices: CRITICAL, ERROR, WARNING, INFO, DEBUG)
    """
    parser = argparse.ArgumentParser("OpenCV Playground")
    parser.add_argument(
        "--image", type=str, help="Path to image to load into playground", default=None
    )
    parser.add_argument(
        "--no-docs",
        action="store_true",
        help="Do not load the doc window",
        default=False,
    )
    parser.add_argument(
        "--disable-info-widgets",
        action="store_true",
        help="Disable all info widgets",
        default=False,
    )
    parser.add_argument(
        "--log-level",
        action="store",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Log Level",
    )
    args = parser.parse_args()
    
    # Use default log level from config if not specified in args
    if args.log_level == "INFO":
        log_level = config.get_default_log_level()
    else:
        log_level = args.log_level
    
    log_level = logging.getLevelName(log_level)
    logging.basicConfig(format=LOG_FORMAT, level=log_level)
    logging.info("Starting OpenCV Playground")
    
    if args.image is not None:
        _validate_image_path(args.image)
        
    run_playground(args)  # GUI related code
