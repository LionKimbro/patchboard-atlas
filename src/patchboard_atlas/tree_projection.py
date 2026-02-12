"""
Tree pane projection for Patchboard Atlas.

Projects ECS state (cmp_entities + cmp_card_ref) into the Tree widget.
Tree is a pure projection — fully reconstructable from ECS state.
"""

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import gui_scaffold


g = {
    "suppress_events": False,
}


def rebuild_tree():
    """Rebuild the Tree widget from current ECS state.

    Full clear-and-rebuild. Preserves selection if the previously
    selected eid still exists after rebuild.
    """
    tree = gui_scaffold.widgets["component-tree"]

    g["suppress_events"] = True

    # capture current selection
    selected = tree.selection()
    prev_eid = selected[0] if selected else None

    # clear tree
    for child in tree.get_children():
        tree.delete(child)

    # insert nodes from ECS
    for eid in sorted(ecs.cmp_entities):
        card = ecs.cmp_card_ref[eid]
        tree.insert(
            "",
            "end",
            iid=str(eid),
            text=card["title"],
            values=(eid, card["inbox"], card["outbox"]),
            tags=("component",),
        )

    # restore selection
    if prev_eid is not None and tree.exists(prev_eid):
        tree.selection_set(prev_eid)

    g["suppress_events"] = False
