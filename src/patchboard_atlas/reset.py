"""
Centralized reset for Patchboard Atlas.

Every module that introduces clearable state must add its
reset call here.
"""

from patchboard_atlas import mem
from patchboard_atlas import log
from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import component_registry
from patchboard_atlas import rendering
from patchboard_atlas import coord_machine as cm
from patchboard_atlas import intent_wires as iw
from patchboard_atlas import router_poll
from patchboard_atlas import gui_tick


def reset():
    """Reset all module state to initial empty condition."""
    mem.clear()
    log.clear_log()
    ecs.reset_ecs()
    component_registry.clear_registry()
    rendering.RENDER.clear()
    rendering.g_drag["mode"] = None
    rendering.g_drag["x"] = 0
    rendering.g_drag["y"] = 0
    rendering.g_drag["eid"] = None
    rendering.g_wire["active"] = False
    rendering.g_wire["from_eid"] = None
    rendering.g_wire["from_channel"] = None
    rendering.g_wire["from_wx"] = None
    rendering.g_wire["from_wy"] = None
    rendering.g_wire["to_wx"] = None
    rendering.g_wire["to_wy"] = None
    rendering.g_wire["over_target"] = False
    rendering.g_hover["wire"] = None
    rendering.g_hover["shift"] = False
    cm.coord_reset_state()
    iw.clear()
    router_poll.reset_poll()
    gui_tick.g["tick_count"] = 0
    gui_tick.g["after_id"] = None
