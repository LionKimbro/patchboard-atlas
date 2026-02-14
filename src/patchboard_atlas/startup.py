"""
Startup loading for Patchboard Atlas.

Orchestrates persisted card loading, validation, tree projection,
and rendering pipeline initialization.
"""

from patchboard_atlas import paths
from patchboard_atlas import component_registry as reg
from patchboard_atlas import tree_projection as tp
from patchboard_atlas import rendering


def startup_load():
    """Load persisted cards, cull invalid ones, rebuild tree, init rendering."""
    paths.component_id_cards_dir().mkdir(parents=True, exist_ok=True)
    reg.load_persisted_cards()
    reg.validate_or_cull_persisted_cards()
    tp.rebuild_tree()
    rendering.bind_canvas_events()
    rendering.sync_all()
