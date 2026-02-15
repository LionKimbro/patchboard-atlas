from tkintertester import harness

from patchboard_atlas import gui_scaffold
from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import tree_projection as tp
from patchboard_atlas import rendering
from patchboard_atlas.reset import reset


def register_rendering_placement_tests():
    harness.add_test(
        "rendering: select tree item and click canvas places component",
        [
            step_setup_entity_and_tree,
            step_select_and_click,
            step_check_placement,
        ],
    )


def _make_card(title, inbox, outbox):
    return {
        "schema_version": 1,
        "title": title,
        "inbox": inbox,
        "outbox": outbox,
        "channels": {"in": [], "out": []},
    }


def step_setup_entity_and_tree():
    reset()
    card = _make_card("Alpha", "C:\\a\\inbox", "C:\\a\\outbox")
    eid = ecs.allocate_entity()
    ecs.cmp_card_ref[eid] = card
    tp.rebuild_tree()
    rendering.bind_canvas_events()
    return ("next", None)


class _FakeEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def step_select_and_click():
    tree = gui_scaffold.widgets["component-tree"]
    tree.selection_set("1")
    rendering.place_selected_component(_FakeEvent(100, 100))
    return ("next", None)


def step_check_placement():
    if 1 not in ecs.cmp_spatial:
        return ("fail", "entity 1 not in cmp_spatial after click")

    canvas = rendering.get_canvas()
    items = canvas.find_withtag("entity|1")
    if not items:
        return ("fail", "no canvas items with tag entity|1")
    if len(items) < 2:
        return ("fail", f"expected at least 2 items (perimeter + title), got {len(items)}")
    return ("next", None)
