"""
Rendering pipeline for Patchboard Atlas.

Three-layer architecture:
  World (ECS)  ->  Render Intent (RENDER)  ->  Canvas Substrate (Tk)

sync_all() is the entry point: rebuild intent, then flush to canvas.
"""

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import gui_scaffold
from patchboard_atlas import coord_machine as cm
from patchboard_atlas import mem
from patchboard_atlas import eid_projection


# ============================================================
# CONSTANTS
# ============================================================

COMPONENT_MIN_HALF_W = 60
HEADER_H = 26
CHANNEL_ROW_H = 18
FOOTER_PAD = 8
PORT_R = 5
CHAR_W_PX = 6       # estimated px per character at Consolas 8pt
COL_INNER_HALF_GAP = 6  # min px from label edge to box center

PERIMETER_OUTLINE = "#4488cc"
PERIMETER_FILL = "#223344"
HEADER_LINE_FILL = "#4488cc"
TITLE_FILL = "#ccddee"
CHANNEL_LABEL_FILL = "#aabbcc"
PORT_FILL = "#4A90E2"
PORT_OUTLINE = "#cccccc"


# ============================================================
# DRAG STATE
# ============================================================

g_drag = {
    "mode": None,      # "pan" | "drag" | None
    "x": 0,            # drag anchor x in world space
    "y": 0,            # drag anchor y in world space
    "eid": None,        # entity being dragged (for future "drag" mode)
}


# ============================================================
# RENDER INTENT
# ============================================================

RENDER = {}


# ============================================================
# CANVAS LOCATION HELPER
# ============================================================

def get_canvas():
    return gui_scaffold.widgets["canvas"]


# ============================================================
# ELEMENT KEY HELPERS
# ============================================================

def ek_to_tag(ek):
    """Serialize an element_key tuple into a canvas tag string."""
    return "ek|" + "|".join(str(part) for part in ek)


def entity_tag(eid):
    """Grouping tag for all canvas items belonging to an entity."""
    return f"entity|{eid}"


def _hit_test_entity():
    """Return the EID of the placed entity under the mouse, or None."""
    canvas = get_canvas()
    items = canvas.find_withtag("current")
    if not items:
        return None
    for tag in canvas.gettags(items[0]):
        if tag.startswith("entity|"):
            return int(tag.split("|")[1])
    return None


# ============================================================
# RULE EXECUTION LOOKUP HELPERS
# ============================================================

def lookup_codes(thing_codes):
    L = []
    spatial = mem.peek("spatial")
    for ch in thing_codes:
        if ch == "#": L.append(mem.peek("eid"))
        elif ch == "C": L.append(mem.peek("card"))
        elif ch == "S": L.append(mem.peek("spatial"))
        elif ch == "x": L.append(spatial["x"])
        elif ch == "y": L.append(spatial["y"])
        elif ch == "t": L.append(mem.peek("card")["title"])  # if you have the card, you have a title
    return L


# ============================================================
# COMPONENT GEOMETRY
# ============================================================

def component_half_h(card):
    """Return half the component height, scaled by channel count."""
    channels = card.get("channels", {}) if card else {}
    n = max(len(channels.get("in", [])), len(channels.get("out", [])), 0)
    return (HEADER_H + n * CHANNEL_ROW_H + FOOTER_PAD) // 2


def component_half_w(card):
    """Return half the component width, scaled by longest channel name."""
    channels = card.get("channels", {}) if card else {}
    all_names = channels.get("in", []) + channels.get("out", [])
    max_len = max((len(n) for n in all_names), default=0)
    needed = PORT_R + 4 + max_len * CHAR_W_PX + COL_INNER_HALF_GAP
    return max(needed, COMPONENT_MIN_HALF_W)


# ============================================================
# RULES
# ============================================================

def rule_perimeter():
    """Emit a perimeter rectangle for a placed entity."""
    if mem.peek("card") is None:
        return
    eid, sx, sy = lookup_codes("#xy")
    card = mem.peek("card")
    half_w = component_half_w(card)
    half_h = component_half_h(card)
    ek = ("entity", eid, "perimeter")
    RENDER[ek] = {
        "type": "rectangle",
        "x0": sx - half_w,
        "y0": sy - half_h,
        "x1": sx + half_w,
        "y1": sy + half_h,
        "outline": PERIMETER_OUTLINE,
        "fill": PERIMETER_FILL,
        "width": 2,
        "tags": (ek_to_tag(ek), entity_tag(eid), "kind|component"),
    }


def rule_header_line():
    """Emit a horizontal separator between the title area and channel rows."""
    if mem.peek("card") is None:
        return
    eid, sx, sy = lookup_codes("#xy")
    card = mem.peek("card")
    half_w = component_half_w(card)
    half_h = component_half_h(card)
    line_y = sy - half_h + HEADER_H
    ek = ("entity", eid, "header-line")
    RENDER[ek] = {
        "type": "line",
        "x0": sx - half_w,
        "y0": line_y,
        "x1": sx + half_w,
        "y1": line_y,
        "fill": HEADER_LINE_FILL,
        "width": 1,
        "tags": (ek_to_tag(ek), entity_tag(eid), "kind|component"),
    }


def rule_title():
    """Emit a title label centered in the header area."""
    if mem.peek("card") is None:
        return
    eid, sx, sy, title = lookup_codes("#xyt")
    card = mem.peek("card")
    half_h = component_half_h(card)
    title_y = sy - half_h + HEADER_H // 2
    ek = ("entity", eid, "title")
    RENDER[ek] = {
        "type": "text",
        "x": sx,
        "y": title_y,
        "text": title,
        "anchor": "center",
        "fill": TITLE_FILL,
        "font": ("Consolas", 10),
        "tags": (ek_to_tag(ek), entity_tag(eid), "kind|component"),
    }


def rule_channels():
    """Emit port ovals and labels for all in/out channels of a placed entity."""
    if mem.peek("card") is None:
        return
    eid, sx, sy = lookup_codes("#xy")
    card = mem.peek("card")
    channels = card.get("channels", {})
    in_channels = channels.get("in", [])
    out_channels = channels.get("out", [])
    half_w = component_half_w(card)
    half_h = component_half_h(card)
    top_y = sy - half_h + HEADER_H

    for i, ch_name in enumerate(in_channels):
        row_y = top_y + i * CHANNEL_ROW_H + CHANNEL_ROW_H // 2
        port_x = sx - half_w

        ek_port = ("entity", eid, "channel-in", ch_name, "port")
        RENDER[ek_port] = {
            "type": "oval",
            "x0": port_x - PORT_R,
            "y0": row_y - PORT_R,
            "x1": port_x + PORT_R,
            "y1": row_y + PORT_R,
            "fill": PORT_FILL,
            "outline": PORT_OUTLINE,
            "tags": (ek_to_tag(ek_port), entity_tag(eid), "kind|component"),
        }

        ek_label = ("entity", eid, "channel-in", ch_name, "label")
        RENDER[ek_label] = {
            "type": "text",
            "x": port_x + PORT_R + 4,
            "y": row_y,
            "text": ch_name,
            "anchor": "w",
            "fill": CHANNEL_LABEL_FILL,
            "font": ("Consolas", 8),
            "tags": (ek_to_tag(ek_label), entity_tag(eid), "kind|component"),
        }

    for i, ch_name in enumerate(out_channels):
        row_y = top_y + i * CHANNEL_ROW_H + CHANNEL_ROW_H // 2
        port_x = sx + half_w

        ek_port = ("entity", eid, "channel-out", ch_name, "port")
        RENDER[ek_port] = {
            "type": "oval",
            "x0": port_x - PORT_R,
            "y0": row_y - PORT_R,
            "x1": port_x + PORT_R,
            "y1": row_y + PORT_R,
            "fill": PORT_FILL,
            "outline": PORT_OUTLINE,
            "tags": (ek_to_tag(ek_port), entity_tag(eid), "kind|component"),
        }

        ek_label = ("entity", eid, "channel-out", ch_name, "label")
        RENDER[ek_label] = {
            "type": "text",
            "x": port_x - PORT_R - 4,
            "y": row_y,
            "text": ch_name,
            "anchor": "e",
            "fill": CHANNEL_LABEL_FILL,
            "font": ("Consolas", 8),
            "tags": (ek_to_tag(ek_label), entity_tag(eid), "kind|component"),
        }


RULES = [rule_perimeter, rule_header_line, rule_title, rule_channels]


# ============================================================
# REBUILD RENDER INTENT
# ============================================================

def rebuild_render_intent():
    """Clear RENDER and recompute from world state."""
    RENDER.clear()
    for eid in sorted(ecs.cmp_entities):
        eid_projection.project_eid(eid)
        if mem.peek("spatial") is None:
            continue
        for rule in RULES:
            rule()


# ============================================================
# FLUSH TO CANVAS
# ============================================================

def _collect_existing_ek_tags():
    """Return set of ek|... tags currently on the canvas."""
    canvas = get_canvas()
    found = set()
    for item_id in canvas.find_withtag("kind|component"):
        for tag in canvas.gettags(item_id):
            if tag.startswith("ek|"):
                found.add(tag)
    return found


def _create_element(desc):
    """Create a bare canvas item with tags. Returns the item ID."""
    canvas = get_canvas()
    if desc["type"] == "rectangle":
        item_id = canvas.create_rectangle(0, 0, 0, 0, tags=desc["tags"])
    elif desc["type"] == "oval":
        item_id = canvas.create_oval(0, 0, 0, 0, tags=desc["tags"])
    elif desc["type"] == "line":
        item_id = canvas.create_line(0, 0, 0, 0, tags=desc["tags"])
    elif desc["type"] == "text":
        item_id = canvas.create_text(0, 0, text="", tags=desc["tags"])
    else:
        raise ValueError(f"_create_element: unknown type '{desc['type']}'")
    return item_id


def _update_element(item_id, desc):
    """Shape and style an existing canvas item from a descriptor."""
    canvas = get_canvas()
    if desc["type"] in ("rectangle", "oval"):
        cm.g_coord["x0"] = desc["x0"]
        cm.g_coord["y0"] = desc["y0"]
        cm.g_coord["x1"] = desc["x1"]
        cm.g_coord["y1"] = desc["y1"]
        cm.g_coord["coord-type"] = "w"
        cm.project_to("c")
        x0, y0, x1, y1 = cm.get_xyxy()

        canvas.coords(item_id, x0, y0, x1, y1)
        if desc["type"] == "rectangle":
            canvas.itemconfigure(item_id,
                                 outline=desc["outline"],
                                 fill=desc["fill"],
                                 width=desc["width"])
        else:
            canvas.itemconfigure(item_id,
                                 outline=desc["outline"],
                                 fill=desc["fill"])

    elif desc["type"] == "line":
        cm.g_coord["x0"] = desc["x0"]
        cm.g_coord["y0"] = desc["y0"]
        cm.g_coord["x1"] = desc["x1"]
        cm.g_coord["y1"] = desc["y1"]
        cm.g_coord["coord-type"] = "w"
        cm.project_to("c")
        x0, y0, x1, y1 = cm.get_xyxy()

        canvas.coords(item_id, x0, y0, x1, y1)
        canvas.itemconfigure(item_id, fill=desc["fill"], width=desc["width"])

    elif desc["type"] == "text":
        cm.set_xy(desc["x"], desc["y"])
        cm.g_coord["coord-type"] = "w"
        cm.project_to("c")
        cx, cy = cm.get_xy()

        canvas.coords(item_id, cx, cy)
        canvas.itemconfigure(item_id,
                             text=desc["text"],
                             fill=desc["fill"],
                             font=desc["font"],
                             anchor=desc.get("anchor", "center"))


def flush_to_canvas():
    """Reconcile RENDER intent against canvas items."""
    canvas = get_canvas()

    declared_tags = set(ek_to_tag(ek) for ek in RENDER)
    existing_tags = _collect_existing_ek_tags()

    # create or update declared elements
    for ek, desc in RENDER.items():
        ek_tag = ek_to_tag(ek)
        items = canvas.find_withtag(ek_tag)
        if not items:
            item_id = _create_element(desc)
        else:
            item_id = items[0]
        _update_element(item_id, desc)

    # delete elements no longer declared
    for old_tag in existing_tags - declared_tags:
        for item_id in canvas.find_withtag(old_tag):
            canvas.delete(item_id)


# ============================================================
# SYNC
# ============================================================

def sync_all():
    """Main entry point: rebuild intent, then flush to canvas."""
    _update_viewport()
    rebuild_render_intent()
    flush_to_canvas()


def _update_viewport():
    """Push current canvas pixel size into the coordinate machine."""
    canvas = get_canvas()
    canvas.update_idletasks()
    cm.set_viewport(canvas.winfo_width(), canvas.winfo_height())


# ============================================================
# EVENT DISPATCH
# ============================================================

def dispatch_event(event, handler_fn):
    """Normalize a raw Tk event into mem context, then call handler.

    Resolves: event object, selected EID, viewport, and world-space
    click position. Handler reads context from mem.peek / coord machine.
    """
    mem.poke("event", event)

    # EID projections:
    eid_projection.project_selected("tree")

    # coordinates machine:
    _update_viewport()
    cm.intake_event(event, "w")  # "w": project to world
    
    handler_fn()


def doit(fn):
    """Wrap a parameterless handler into a Tk-compatible callback."""
    return lambda e: dispatch_event(e, fn)


# ============================================================
# PLACEMENT
# ============================================================

def place_selected_component():
    """Place the selected tree component at the dispatched click position."""
    eid = mem.peek("eid")
    if eid is None:
        return

    # already placed -- ignore
    if eid in ecs.cmp_spatial:
        return

    wx, wy = cm.get_xy()
    ecs.cmp_spatial[eid] = {"x": wx, "y": wy}

    sync_all()
    gui_scaffold.set_status(f"Placed entity {eid} at ({wx}, {wy})", gui_scaffold.GREEN)


# ============================================================
# DRAG
# ============================================================

def start_pan():
    """Begin a pan drag from the current world-space position."""
    g_drag["mode"] = "pan"
    g_drag["x"], g_drag["y"] = cm.get_xy()


def start_drag_component(eid):
    """Begin a note drag on the given entity."""
    g_drag["mode"] = "drag"
    g_drag["eid"] = eid
    g_drag["x"], g_drag["y"] = cm.get_xy()


def cancel_drag():
    """Clear drag state without applying any final action."""
    g_drag["mode"] = None


# ============================================================
# CANVAS EVENT HANDLERS
# ============================================================

def on_canvas_button_press():
    """Decision point for Button-1: place, drag note, or pan."""
    eid = mem.peek("eid")
    if eid is not None and eid not in ecs.cmp_spatial:
        place_selected_component()
        return
    hit_eid = _hit_test_entity()
    if hit_eid is not None:
        start_drag_component(hit_eid)
    else:
        start_pan()


def on_canvas_motion():
    """Handle B1-Motion: pan or drag note."""
    mode = g_drag["mode"]
    if mode == "pan":
        wx, wy = cm.get_xy()
        cm.g_cam["x"] -= wx - g_drag["x"]
        cm.g_cam["y"] -= wy - g_drag["y"]
        sync_all()
    elif mode == "drag":
        wx, wy = cm.get_xy()
        dx = wx - g_drag["x"]
        dy = wy - g_drag["y"]
        eid = g_drag["eid"]
        spatial = ecs.cmp_spatial.get(eid)
        if spatial is None:
            cancel_drag()
            return
        spatial["x"] += dx
        spatial["y"] += dy
        g_drag["x"] = wx
        g_drag["y"] = wy
        sync_all()


def on_canvas_button_release():
    """Handle ButtonRelease-1: end any drag."""
    g_drag["mode"] = None


# ============================================================
# BINDINGS
# ============================================================

def bind_canvas_events():
    """Attach rendering-related event bindings to the canvas."""
    canvas = get_canvas()
    canvas.bind("<Button-1>", doit(on_canvas_button_press))
    canvas.bind("<B1-Motion>", doit(on_canvas_motion))
    canvas.bind("<ButtonRelease-1>", doit(on_canvas_button_release))
    canvas.bind("<Configure>", lambda e: sync_all())
