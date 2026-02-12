"""
Startup loading for Patchboard Atlas.

Orchestrates persisted card loading, validation, and tree projection.
"""

from patchboard_atlas import paths
from patchboard_atlas import component_registry as reg
from patchboard_atlas import tree_projection as tp


def startup_load():
    """Load persisted cards, cull invalid ones, rebuild tree."""
    paths.component_id_cards_dir().mkdir(parents=True, exist_ok=True)
    reg.load_persisted_cards()
    reg.validate_or_cull_persisted_cards()
    tp.rebuild_tree()
