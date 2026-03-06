"""
Router topology polling for Patchboard Atlas.

Reads routes.json at two speeds:
  - Default: every 50 ticks (5s at 10 Hz)
  - Fast:    every 3 ticks (0.3s), triggered after sending a request
"""

import json
import os
from pathlib import Path

import lionscliapp as app

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import intent_wires as iw


FAST_POLL_TICKS = 3
DEFAULT_POLL_TICKS = 50
FAST_MODE_DURATION_TICKS = 50

g = {
    "next_poll_tick": 0,
    "fast_mode": False,
    "fast_mode_until": 0,
}

confirmed_routes = []  # list of (source_folder, source_channel, dest_folder, dest_channel)


def enter_fast_mode():
    """Switch to fast polling. Call immediately after sending a router request."""
    from patchboard_atlas import gui_tick
    g["fast_mode"] = True
    g["fast_mode_until"] = gui_tick.g["tick_count"] + FAST_MODE_DURATION_TICKS
    g["next_poll_tick"] = 0


def on_tick(tick_count):
    """Called once per tick. Polls at the appropriate interval."""
    if g["fast_mode"] and tick_count >= g["fast_mode_until"]:
        g["fast_mode"] = False
    if tick_count < g["next_poll_tick"]:
        return
    _do_poll()
    interval = FAST_POLL_TICKS if g["fast_mode"] else DEFAULT_POLL_TICKS
    g["next_poll_tick"] = tick_count + interval


def _do_poll():
    routes_path = app.ctx.get("path.router.routes")
    if not routes_path:
        return
    try:
        text = Path(routes_path).read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, IOError, json.JSONDecodeError):
        return
    routes = data.get("routes", [])
    _update_confirmed_routes(routes)
    _reconcile_intent_wires(routes)
    from patchboard_atlas import rendering
    rendering.sync_all()


def _update_confirmed_routes(routes):
    confirmed_routes.clear()
    for route in routes:
        confirmed_routes.append((
            route.get("source-folder", ""),
            route.get("source-channel", ""),
            route.get("destination-folder", ""),
            route.get("destination-channel", ""),
        ))


def _reconcile_intent_wires(routes):
    to_remove = []
    for wire in iw.intent_wires:
        from_card = ecs.cmp_card_ref.get(wire["from_eid"])
        to_card = ecs.cmp_card_ref.get(wire["to_eid"])
        if from_card is None or to_card is None:
            continue
        from_outbox = os.path.normcase(from_card["outbox"])
        to_inbox = os.path.normcase(to_card["inbox"])
        for route in routes:
            sf = os.path.normcase(route.get("source-folder", ""))
            sc = route.get("source-channel", "")
            df = os.path.normcase(route.get("destination-folder", ""))
            dc = route.get("destination-channel", "")
            if (sf == from_outbox and sc == wire["from_channel"] and
                    df == to_inbox and dc == wire["to_channel"]):
                to_remove.append((
                    wire["from_eid"], wire["from_channel"],
                    wire["to_eid"], wire["to_channel"],
                ))
                break
    for key in to_remove:
        iw.remove_by_key(*key)


def reset_poll():
    """Reset all polling state."""
    g["next_poll_tick"] = 0
    g["fast_mode"] = False
    g["fast_mode_until"] = 0
    confirmed_routes.clear()
