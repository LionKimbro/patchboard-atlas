"""
Entity projection layer for Patchboard Atlas.

Responsible for projecting an EID into mem registers
in a coherent, atomic way.

mem remains dumb.
Projection remains explicit.
"""

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import mem
from patchboard_atlas import gui_scaffold


# ============================================================
# RESOLUTION
# ============================================================

def resolve_tree_selected_eid():
    """
    Return the currently selected EID from the component tree,
    or None if nothing is selected.
    """
    tree = gui_scaffold.widgets.get("component-tree")
    if tree is None:
        return None

    selected = tree.selection()
    return int(selected[0]) if selected else None


# ============================================================
# PROJECTION
# ============================================================

def project_eid(eid):
    """
    Atomically project an EID into mem.

    Guarantees:
        mem["eid"]
        mem["spatial"]
        mem["card"]

    All coherent for the provided EID (or None).
    """
    mem.poke("eid", eid)

    if eid is None:
        mem.poke("spatial", None)
        mem.poke("card", None)
        return

    mem.poke("spatial", ecs.cmp_spatial.get(eid))
    mem.poke("card", ecs.cmp_card_ref.get(eid))


def project_selected(source="tree"):
    """
    Project the currently selected EID.

    'source' allows future expansion if multiple selection
    mechanisms exist.
    """
    if source == "tree":
        eid = resolve_tree_selected_eid()
    else:
        raise ValueError(f"Unknown selection source: {source}")

    project_eid(eid)

