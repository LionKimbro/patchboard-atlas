"""
Periodic 10Hz tick for Patchboard Atlas.

start() launches the tick loop after the GUI is created.
stop() cancels it before the GUI is torn down.
The after_id of the pending callback is kept in g["after_id"].
"""

from patchboard_atlas import gui_scaffold

TICK_MS = 100  # 10 Hz

g = {
    "after_id": None,
}


def _call_per_tick():
    pass


def _tick():
    _call_per_tick()
    root = gui_scaffold.widgets.get("root")
    if root is None:
        g["after_id"] = None
        return
    g["after_id"] = root.after(TICK_MS, _tick)


def start():
    """Schedule the first tick. Call once after the GUI is created."""
    root = gui_scaffold.widgets.get("root")
    if root is None:
        return
    g["after_id"] = root.after(TICK_MS, _tick)


def stop():
    """Cancel the pending tick. Safe to call multiple times."""
    after_id = g["after_id"]
    g["after_id"] = None
    if after_id is None:
        return
    root = gui_scaffold.widgets.get("root")
    if root is not None:
        root.after_cancel(after_id)
