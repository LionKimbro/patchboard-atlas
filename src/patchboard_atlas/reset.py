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


def reset():
    """Reset all module state to initial empty condition."""
    mem.clear()
    log.clear_log()
    ecs.reset_ecs()
    component_registry.clear_registry()
    rendering.RENDER.clear()
    cm.coord_reset_state()
