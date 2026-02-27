"""Melody Architect: symbolic melody analysis and arrangement planning."""

from .composition import build_composition_document
from .logic_export import create_logic_project_bundle
from .midi_pack import generate_midi_pack
from .pipeline import analyze_file, analyze_melody_data, load_input_file

__all__ = [
    "analyze_file",
    "analyze_melody_data",
    "load_input_file",
    "create_logic_project_bundle",
    "build_composition_document",
    "generate_midi_pack",
]
