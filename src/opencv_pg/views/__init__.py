import logging

# Initialize logging for the views module
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Import key components to make them accessible from the views module
from .pipeline_window import PipeWindow
from .playground import Playground

log.info("Views module initialized")
