from .pipeline_launcher import launch_pipeline

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("docs/source_docs"),
    autoescape=select_autoescape(["html"]),
)

def get_env():
    """
    Returns the Jinja2 environment instance.
    """
    return env

# Make all common classes available at package level with direct imports
from .models.pipeline import Pipeline
from .models.window import Window
from .models.base_transform import BaseTransform
from .models import params
from .models.params import Param
from .models import transforms
from .models import support_transforms
