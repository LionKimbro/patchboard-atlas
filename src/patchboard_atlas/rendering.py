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


# ============================================================
# CONSTANTS
# ============================================================

COMPONENT_W = 120
COMPONENT_H = 60

PERIMETER_OUTLINE = "#4488cc"
PERIMETER_FILL = "#223344"
TITLE_FILL = "#ccddee"


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


# ============================================================
# RULE EXECUTION LOOKUP HELPERS
# ============================================================

def keep_codes(eid):
    mem.poke("eid", eid)
    mem.poke("spatial", ecs.cmp_spatial[eid])  # required for rebuild_render_intent ecs
    mem.poke("card", ecs.cmp_card_ref.get(eid))  

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
# RULES
# ============================================================

def rule_perimeter():
    """Emit a perimeter rectangle for a placed entity."""
    if mem.peek("card") is None:
        return
    eid, sx, sy = lookup_codes("#xy")
    half_w = COMPONENT_W // 2
    half_h = COMPONENT_H // 2
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


def rule_title():
    """Emit a title label for a placed entity."""
    if mem.peek("card") is None:
        return
    eid, sx, sy, title = lookup_codes("#xyt")
    ek = ("entity", eid, "title")
    RENDER[ek] = {
        "type": "text",
        "x": sx,
        "y": sy,
        "text": title,
        "fill": TITLE_FILL,
        "font": ("Consolas", 10),
        "tags": (ek_to_tag(ek), entity_tag(eid), "kind|component"),
    }


RULES = [rule_perimeter, rule_title]


# ============================================================
# REBUILD RENDER INTENT
# ============================================================

def rebuild_render_intent():
    """Clear RENDER and recompute from world state."""
    RENDER.clear()
    for eid in sorted(ecs.cmp_entities):
        spatial = ecs.cmp_spatial.get(eid)
        if spatial is None:
            continue
        keep_codes(eid)
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
    elif desc["type"] == "text":
        item_id = canvas.create_text(0, 0, text="", tags=desc["tags"])
    else:
        raise ValueError(f"_create_element: unknown type '{desc['type']}'")
    return item_id


def _update_element(item_id, desc):
    """Shape and style an existing canvas item from a descriptor."""
    canvas = get_canvas()
    if desc["type"] == "rectangle":
        cm.g_coord["x0"] = desc["x0"]
        cm.g_coord["y0"] = desc["y0"]
        cm.g_coord["x1"] = desc["x1"]
        cm.g_coord["y1"] = desc["y1"]
        cm.g_coord["coord-type"] = "w"
        cm.project_to("c")
        x0, y0, x1, y1 = cm.get_xyxy()

        canvas.coords(item_id, x0, y0, x1, y1)
        canvas.itemconfigure(item_id,
                             outline=desc["outline"],
                             fill=desc["fill"],
                             width=desc["width"])

    elif desc["type"] == "text":
        cm.set_xy(desc["x"], desc["y"])
        cm.g_coord["coord-type"] = "w"
        cm.project_to("c")
        cx, cy = cm.get_xy()

        canvas.coords(item_id, cx, cy)
        canvas.itemconfigure(item_id,
                             text=desc["text"],
                             fill=desc["fill"],
                             font=desc["font"])


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
# PLACEMENT
# ============================================================

def place_selected_component(event):
    """Canvas click handler: place the selected tree component at click position."""
    tree = gui_scaffold.widgets.get("component-tree")
    if tree is None:
        return

    selected = tree.selection()
    if not selected:
        return

    eid = int(selected[0])

    # already placed -- ignore
    if eid in ecs.cmp_spatial:
        return

    # ensure viewport is current before unprojecting
    _update_viewport()

    # unproject canvas click to world coords
    cm.g_event["x"] = event.x
    cm.g_event["y"] = event.y
    cm.load_pt("event")
    cm.project_to("w")
    wx, wy = cm.get_xy()

    ecs.cmp_spatial[eid] = {"x": wx, "y": wy}

    sync_all()
    gui_scaffold.set_status(f"Placed entity {eid} at ({wx}, {wy})", gui_scaffold.GREEN)


# ============================================================
# BINDINGS
# ============================================================

def bind_canvas_events():
    """Attach rendering-related event bindings to the canvas."""
    canvas = get_canvas()
    canvas.bind("<Button-1>", place_selected_component)
