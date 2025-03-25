import logging
from pathlib import Path
import os

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

log = logging.getLogger(__name__)

ROOT = Path(__file__)
RENDERED_DIR = ROOT.parent.joinpath("rendered_docs/")
TEMPLATE_DIR = ROOT.parent.joinpath("templates/")
print(RENDERED_DIR)
print(TEMPLATE_DIR)

# Create Jinja2 environment for templates
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def _create_rendered_docs():
    """Create rendered_docs folder if it doesn't exist"""
    if not RENDERED_DIR.exists():
        RENDERED_DIR.mkdir()
        log.info("Created %s", RENDERED_DIR)
    
    # Also ensure template dir exists
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir()
        log.info("Created %s", TEMPLATE_DIR)


def get_template(template_name):
    """Helper to get a template, falling back to error template if not found"""
    try:
        return env.get_template(template_name)
    except TemplateNotFound:
        return env.get_template("error.html")


def render_local_doc(folder, doc_fname):
    """Renders template into a local file

    Normally we would render content in the webview with `setHtml`, but there
    seems to be a bug which doesn't load local resources when that method is
    used. It works properly when loaded from a local file.
    """
    try:
        template = env.get_template(doc_fname)
        log.error(f"Template not found: {template}")
        html = template.render()
    except TemplateNotFound:
        # Create a simple error template if none exists
        html = f"<html><body><h1>Error</h1><p>Template: {doc_fname} not found :(</p></body></html>"
        log.error(f"Template not found: {doc_fname}")

    path = folder.joinpath(doc_fname)
    print(path)
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(html)
        log.debug("Wrote Doc: %s", path)

# Create rendered docs folder if it doesn't exist
_create_rendered_docs()
