from tkintertester import harness

from patchboard_atlas import gui_scaffold
from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import tree_projection as tp
from patchboard_atlas.reset import reset


def register_tree_projection_tests():
    harness.add_test(
        "tree projection: component-tree widget exists",
        [
            step_check_component_tree_exists,
        ],
    )

    harness.add_test(
        "tree projection: menu bar exists",
        [
            step_check_menu_bar_exists,
        ],
    )

    harness.add_test(
        "tree projection: rebuild empty",
        [
            step_rebuild_empty_tree,
        ],
    )

    harness.add_test(
        "tree projection: rebuild with entities",
        [
            step_add_entities_and_rebuild,
            step_check_tree_has_nodes,
        ],
    )

    harness.add_test(
        "tree projection: rebuild clears old nodes",
        [
            step_add_entities_and_rebuild,
            step_remove_entity_and_rebuild,
            step_check_tree_has_one_node,
        ],
    )

    harness.add_test(
        "tree projection: rebuild preserves selection",
        [
            step_add_entities_and_rebuild,
            step_select_second_entity,
            step_rebuild_and_check_selection_preserved,
        ],
    )


# --- steps ---

def step_check_component_tree_exists():
    tree = gui_scaffold.widgets.get("component-tree")
    if tree is None or not tree.winfo_exists():
        return ("fail", "missing component-tree widget")
    return ("next", None)


def step_check_menu_bar_exists():
    menu_bar = gui_scaffold.widgets.get("menu-bar")
    if menu_bar is None:
        return ("fail", "missing menu-bar widget")
    file_menu = gui_scaffold.widgets.get("file-menu")
    if file_menu is None:
        return ("fail", "missing file-menu widget")
    return ("next", None)


def step_rebuild_empty_tree():
    reset()
    tp.rebuild_tree()
    tree = gui_scaffold.widgets["component-tree"]
    children = tree.get_children()
    if len(children) != 0:
        return ("fail", f"expected 0 children, got {len(children)}")
    return ("next", None)


def _make_card(title, inbox, outbox):
    return {
        "schema_version": 1,
        "title": title,
        "inbox": inbox,
        "outbox": outbox,
        "channels": {"in": [], "out": []},
    }


def step_add_entities_and_rebuild():
    reset()
    card_a = _make_card("Alpha", "C:\\a\\inbox", "C:\\a\\outbox")
    card_b = _make_card("Beta", "C:\\b\\inbox", "C:\\b\\outbox")

    eid1 = ecs.allocate_entity()
    ecs.cmp_card_ref[eid1] = card_a
    eid2 = ecs.allocate_entity()
    ecs.cmp_card_ref[eid2] = card_b

    tp.rebuild_tree()
    return ("next", None)


def step_check_tree_has_nodes():
    tree = gui_scaffold.widgets["component-tree"]
    children = tree.get_children()
    if len(children) != 2:
        return ("fail", f"expected 2 children, got {len(children)}")
    text_1 = tree.item(children[0], "text")
    text_2 = tree.item(children[1], "text")
    if text_1 != "Alpha":
        return ("fail", f"expected 'Alpha', got '{text_1}'")
    if text_2 != "Beta":
        return ("fail", f"expected 'Beta', got '{text_2}'")
    return ("next", None)


def step_remove_entity_and_rebuild():
    ecs.remove_entity(1)
    tp.rebuild_tree()
    return ("next", None)


def step_check_tree_has_one_node():
    tree = gui_scaffold.widgets["component-tree"]
    children = tree.get_children()
    if len(children) != 1:
        return ("fail", f"expected 1 child, got {len(children)}")
    text = tree.item(children[0], "text")
    if text != "Beta":
        return ("fail", f"expected 'Beta', got '{text}'")
    return ("next", None)


def step_select_second_entity():
    tree = gui_scaffold.widgets["component-tree"]
    tree.selection_set("2")
    return ("next", None)


def step_rebuild_and_check_selection_preserved():
    tp.rebuild_tree()
    tree = gui_scaffold.widgets["component-tree"]
    selected = tree.selection()
    if not selected or selected[0] != "2":
        return ("fail", f"expected selection '2', got {selected}")
    return ("next", None)
