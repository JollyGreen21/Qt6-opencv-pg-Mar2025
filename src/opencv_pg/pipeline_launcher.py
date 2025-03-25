import logging
from PySide6 import QtWidgets  # GUI library import
from models.pipeline import Pipeline
from views.pipeline_window import PipeWindow  # GUI window import
from utils.config_manager import config  # Add this import

def launch_pipeline(pipeline: Pipeline, show_info_widgets: bool = False,
                    log_level=logging.INFO):
    """Opens a PipelineWindow for each Window in the Pipeline

    Args:
        pipeline (Pipeline): Incoming Pipeline
        show_info_widgets (bool): If True, shows info_widgets on Transforms.
            Default is False.
        log_level (logging.LEVEL_NAME): Log level to use. Default is INFO.
    """
    # Configure logging with format from config
    logging.basicConfig(format=config.get_log_format(), level=log_level)
    
    # Get or create QApplication instance (GUI application)
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # Have to keep windows in scope to show them, so store them in a list
    windows = []
    for window in pipeline.windows:
        pipe_win = PipeWindow(window, show_info_widget=show_info_widgets)  # Create GUI window
        pipe_win.resize(*config.get_pipeline_window_size())  # Use config value
        pipe_win.show()  # Show window
        windows.append(pipe_win)  # Add window to list to keep in scope

    # Process events before running pipeline (GUI event processing)
    app.processEvents()
    pipeline.run_pipeline()

    # Reset each viewer so image is fit to its size
    last_pos = None
    for win in windows:
        win.set_splitter_pos(config.get_pipeline_split_percentage())  # Use config value
        win.viewer.reset_view()  # Reset GUI viewer

        # Stagger windows (GUI window positioning)
        if last_pos is None:
            last_pos = (win.x(), win.y())
        else:
            offset = config.get_pipeline_window_offset()  # Use config value
            win.move(last_pos[0] + offset, last_pos[1] + offset)
            last_pos = (win.x(), win.y())  # Update for next window
    
    return app  # Return app so it can be used by the caller

# Execute the app only if run as main script
if __name__ == "__main__":
    # Create a simple pipeline example
    from models.pipeline import Pipeline
    from models.window import Window
    
    # Create a basic pipeline for demonstration
    pipeline = Pipeline([Window([])])
    app = launch_pipeline(pipeline)
    app.exec()  # Use exec() instead of exec_() in newer PySide6
