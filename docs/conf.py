"""cap_inspector Sphinx documentation configuration."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

project = "cap_inspector"
version = ""
release = ""

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
napoleon_google_docstring = True
# Documentation builds should not require physical cameras or running gRPC services.
autodoc_mock_imports = [
    "cv2", "numpy", "x_logger", "grpc_frame", "grpc", "PySide6",
]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": False,
}
exclude_patterns = ["_build", "_build_source"]
html_static_path = []
master_doc = "index"
