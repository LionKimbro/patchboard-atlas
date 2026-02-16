from tkintertester import harness

from patchboard_atlas import rendering
from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import coord_machine as cm
from patchboard_atlas import startup
from patchboard_atlas.reset import reset


def register_rendering_drag_tests():
    harness.add_test(
        "rendering: drag moves placed component",
        [
            step_setup,
            step_place_component,
            step_drag_component,
            step_check_result,
        ],
    )


class _FakeEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def step_setup():
    reset()
    startup.startup_load()
    cm.set_viewport(800, 600)
    return ("next", None)


def step_place_component():
    # Create an entity with a card and spatial placement directly
    eid = ecs.allocate_entity()
    ecs.cmp_card_ref[eid] = {"title": "DragTest"}
    ecs.cmp_spatial[eid] = {"x": 200, "y": 100}
    rendering.sync_all()

    harness.g["_drag_test_eid"] = eid
    return ("next", None)


def step_drag_component():
    eid = harness.g["_drag_test_eid"]

    # Start drag note via dispatch (hit_test relies on Tk "current" tag
    # which needs a real pointer, so we call start_drag_note directly)
    cm.set_viewport(800, 600)
    rendering.dispatch_event(
        _FakeEvent(200, 100),
        lambda: rendering.start_drag_note(eid),
    )

    if rendering.g_drag["mode"] != "note":
        return ("fail", f"expected drag mode 'note', got {rendering.g_drag['mode']!r}")

    # Motion: shift 30px right, 20px down in canvas (== world at zoom 1:1)
    rendering.dispatch_event(_FakeEvent(230, 120), rendering.on_canvas_motion)

    # Release
    rendering.dispatch_event(_FakeEvent(230, 120), rendering.on_canvas_button_release)
    return ("next", None)


def step_check_result():
    eid = harness.g.pop("_drag_test_eid")

    if rendering.g_drag["mode"] is not None:
        return ("fail", f"drag mode should be None after release, got {rendering.g_drag['mode']!r}")

    spatial = ecs.cmp_spatial.get(eid)
    if spatial is None:
        return ("fail", "entity lost its spatial component")

    if spatial["x"] != 230:
        return ("fail", f"expected spatial x == 230, got {spatial['x']}")
    if spatial["y"] != 120:
        return ("fail", f"expected spatial y == 120, got {spatial['y']}")
    return ("next", None)
