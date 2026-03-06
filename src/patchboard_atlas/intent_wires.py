"""
Intent wire storage for Patchboard Atlas.

Intent wires are temporary visual indicators of pending connection
requests, displayed while waiting for router confirmation.
"""

FADE_TICKS = 50  # 5 seconds at 10 Hz

intent_wires = []


def add(from_eid, from_channel, to_eid, to_channel, creation_tick):
    """Append a new intent wire."""
    intent_wires.append({
        "from_eid": from_eid,
        "from_channel": from_channel,
        "to_eid": to_eid,
        "to_channel": to_channel,
        "creation_tick": creation_tick,
    })


def remove_by_key(from_eid, from_channel, to_eid, to_channel):
    """Remove all intent wires matching the given endpoints."""
    intent_wires[:] = [
        w for w in intent_wires
        if not (w["from_eid"] == from_eid and
                w["from_channel"] == from_channel and
                w["to_eid"] == to_eid and
                w["to_channel"] == to_channel)
    ]


def fade_alpha(wire, tick_count):
    """Return fade alpha: 1.0 = white-hot (fresh), 0.0 = fully faded."""
    elapsed = tick_count - wire["creation_tick"]
    return max(0.0, 1.0 - elapsed / FADE_TICKS)


def lerp_color(alpha):
    """Interpolate from dim blue (alpha=0.0) to white-hot (alpha=1.0)."""
    r0, g0, b0 = 0x1e, 0x3a, 0x5f  # dim blue
    r1, g1, b1 = 0xff, 0xff, 0xff  # white hot
    r = int(r0 + (r1 - r0) * alpha)
    g = int(g0 + (g1 - g0) * alpha)
    b = int(b0 + (b1 - b0) * alpha)
    return f"#{r:02x}{g:02x}{b:02x}"


def on_tick(tick_count):
    """Drive fade animation. Call rendering sync if any intent wires are live."""
    if not intent_wires:
        return
    from patchboard_atlas import rendering
    rendering.sync_all()


def clear():
    """Remove all intent wires."""
    del intent_wires[:]
