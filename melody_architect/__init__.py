"""Melody Architect: symbolic melody analysis and arrangement planning."""

from .logic_export import create_logic_project_bundle
from .pipeline import analyze_file, analyze_melody_data, load_input_file

__all__ = ["analyze_file", "analyze_melody_data", "load_input_file", "create_logic_project_bundle"]
