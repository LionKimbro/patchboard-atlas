from tkintertester import harness

from patchboard_atlas import rendering
from patchboard_atlas import coord_machine as cm
from patchboard_atlas.reset import reset


def register_rendering_pan_tests():
    harness.add_test(
        "rendering: click-drag pans camera",
        [
            step_setup,
            step_press_motion_release,
            step_check_camera,
        ],
    )


class _FakeEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def step_setup():
    reset()
    rendering.bind_canvas_events()
    cm.set_viewport(800, 600)
    return ("next", None)


def step_press_motion_release():
    rendering.dispatch_event(_FakeEvent(100, 100), rendering.on_canvas_button_press)

    if rendering.g_drag["mode"] != "pan":
        return ("fail", f"expected drag mode 'pan', got {rendering.g_drag['mode']!r}")

    rendering.dispatch_event(_FakeEvent(150, 150), rendering.on_canvas_motion)
    rendering.dispatch_event(_FakeEvent(150, 150), rendering.on_canvas_button_release)
    return ("next", None)


def step_check_camera():
    if rendering.g_drag["mode"] is not None:
        return ("fail", f"drag mode should be None after release, got {rendering.g_drag['mode']!r}")

    # At zoom 1:1, dragging +50px in canvas should shift camera by -50 in world
    if cm.g_cam["x"] != -50:
        return ("fail", f"expected cam x == -50, got {cm.g_cam['x']}")
    if cm.g_cam["y"] != -50:
        return ("fail", f"expected cam y == -50, got {cm.g_cam['y']}")
    return ("next", None)
