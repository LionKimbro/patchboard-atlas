"""
Coordinate machine for Patchboard Atlas.

Procedural, global-state oriented, and camera-aware.
"""

# ============================================================
# GLOBAL STATE
# ============================================================

g_coord = {
    "x": 0,
    "y": 0,
    "x0": 0,
    "y0": 0,
    "x1": 0,
    "y1": 0,
    "coord-type": "w",  # "w" or "c"
}

g_cam = {
    "x": 0,
    "y": 0,
    "zoom-num": 1,
    "zoom-den": 1,
}

g_view = {
    "canvas-view-w": 0,
    "canvas-view-h": 0,
}

g_attachment = {
    "bbox": (0, 0, 0, 0),
}

g_label = {
    "coord": (0, 0),
}

g_event = {
    "x": 0,
    "y": 0,
}

S = []


# ============================================================
# STATE RESET / SETTERS
# ============================================================

def coord_reset_state():
    """
    Reset coord registers, camera, viewport, and stack to defaults.
    """
    g_coord["x"] = 0
    g_coord["y"] = 0
    g_coord["x0"] = 0
    g_coord["y0"] = 0
    g_coord["x1"] = 0
    g_coord["y1"] = 0
    g_coord["coord-type"] = "w"

    g_cam["x"] = 0
    g_cam["y"] = 0
    g_cam["zoom-num"] = 1
    g_cam["zoom-den"] = 1

    g_view["canvas-view-w"] = 0
    g_view["canvas-view-h"] = 0

    g_attachment["bbox"] = (0, 0, 0, 0)
    g_label["coord"] = (0, 0)
    g_event["x"] = 0
    g_event["y"] = 0

    S[:] = []


def set_zoom(zoom_num, zoom_den):
    """
    Set zoom ratio using integer numerator/denominator.
    """
    g_cam["zoom-num"] = zoom_num
    g_cam["zoom-den"] = zoom_den


def set_viewport(canvas_view_w, canvas_view_h):
    """
    Set canvas viewport width/height in pixels.
    """
    g_view["canvas-view-w"] = canvas_view_w
    g_view["canvas-view-h"] = canvas_view_h


def set_xy(x, y):
    """
    Set point registers directly.
    """
    g_coord["x"] = x
    g_coord["y"] = y


# ============================================================
# LOAD / STORE
# ============================================================

def load_rect(src):
    """
    Load rectangle into rect registers.

    src:
        "attachment" -> g_attachment["bbox"]

    Effects:
        g_coord["x0"], g_coord["y0"], g_coord["x1"], g_coord["y1"] set
        g_coord["coord-type"] set to "w"
    """
    if src == "attachment":
        x0, y0, x1, y1 = g_attachment["bbox"]
        g_coord["x0"] = x0
        g_coord["y0"] = y0
        g_coord["x1"] = x1
        g_coord["y1"] = y1
        g_coord["coord-type"] = "w"
    else:
        raise ValueError(f"load_rect: unknown src '{src}'")


def store_rect(dst):
    """
    Store rect registers into world data.

    dst:
        "attachment" -> g_attachment["bbox"]

    Requires:
        g_coord["coord-type"] == "w"
    """
    if dst == "attachment":
        if g_coord.get("coord-type") != "w":
            raise RuntimeError("store_rect: coord-type must be 'w' to store to attachment")

        g_attachment["bbox"] = (
            g_coord["x0"],
            g_coord["y0"],
            g_coord["x1"],
            g_coord["y1"],
        )
    else:
        raise ValueError(f"store_rect: unknown dst '{dst}'")


def load_pt(src):
    """
    Load point into point registers.

    src:
        "event" -> g_event["x"], g_event["y"] (canvas coords)
        "center" | "center-south"
        "nw" | "ne" | "se" | "sw"
        "label" -> g_label["coord"]
    """
    if src == "event":
        g_coord["x"] = g_event["x"]
        g_coord["y"] = g_event["y"]
        g_coord["coord-type"] = "c"
        return

    x0 = g_coord["x0"]
    y0 = g_coord["y0"]
    x1 = g_coord["x1"]
    y1 = g_coord["y1"]

    if src == "center":
        g_coord["x"] = (x0 + x1) // 2
        g_coord["y"] = (y0 + y1) // 2
    elif src == "center-south":
        g_coord["x"] = (x0 + x1) // 2
        g_coord["y"] = y1
    elif src == "nw":
        g_coord["x"] = x0
        g_coord["y"] = y0
    elif src == "ne":
        g_coord["x"] = x1
        g_coord["y"] = y0
    elif src == "se":
        g_coord["x"] = x1
        g_coord["y"] = y1
    elif src == "sw":
        g_coord["x"] = x0
        g_coord["y"] = y1
    elif src == "label":
        g_coord["x"], g_coord["y"] = g_label["coord"]
        g_coord["coord-type"] = "w"
    else:
        raise ValueError(f"load_pt: unknown src '{src}'")


def store_pt(dst):
    """
    Store point registers into a destination.

    dst:
        "nw" | "ne" | "se" | "sw" | "center" | "cam"
    """
    x = g_coord["x"]
    y = g_coord["y"]

    if dst == "center":
        x0 = g_coord["x0"]
        y0 = g_coord["y0"]
        x1 = g_coord["x1"]
        y1 = g_coord["y1"]
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        dx = x - cx
        dy = y - cy
        g_coord["x0"] = x0 + dx
        g_coord["y0"] = y0 + dy
        g_coord["x1"] = x1 + dx
        g_coord["y1"] = y1 + dy
        return

    if dst == "nw":
        g_coord["x0"] = x
        g_coord["y0"] = y
    elif dst == "ne":
        g_coord["x1"] = x
        g_coord["y0"] = y
    elif dst == "se":
        g_coord["x1"] = x
        g_coord["y1"] = y
    elif dst == "sw":
        g_coord["x0"] = x
        g_coord["y1"] = y
    elif dst == "cam":
        g_cam["x"] = x
        g_cam["y"] = y
    else:
        raise ValueError(f"store_pt: unknown dst '{dst}'")


# ============================================================
# PROJECTION
# ============================================================

def project_to(dst):
    """
    Project all registers to new coordinate space.

    dst:
        "c" -> project world -> canvas (apply camera + viewport + zoom)
        "w" -> unproject canvas -> world
    """
    src = g_coord.get("coord-type")
    if src == dst:
        return

    cam_x = g_cam["x"]
    cam_y = g_cam["y"]
    zn = g_cam["zoom-num"]
    zd = g_cam["zoom-den"]

    vcx = g_view["canvas-view-w"] // 2
    vcy = g_view["canvas-view-h"] // 2

    def w_to_c(x, y):
        return (
            ((x - cam_x) * zn) // zd + vcx,
            ((y - cam_y) * zn) // zd + vcy,
        )

    def c_to_w(x, y):
        return (
            ((x - vcx) * zd) // zn + cam_x,
            ((y - vcy) * zd) // zn + cam_y,
        )

    if src == "w" and dst == "c":
        g_coord["x"], g_coord["y"] = w_to_c(g_coord["x"], g_coord["y"])
        g_coord["x0"], g_coord["y0"] = w_to_c(g_coord["x0"], g_coord["y0"])
        g_coord["x1"], g_coord["y1"] = w_to_c(g_coord["x1"], g_coord["y1"])
    elif src == "c" and dst == "w":
        g_coord["x"], g_coord["y"] = c_to_w(g_coord["x"], g_coord["y"])
        g_coord["x0"], g_coord["y0"] = c_to_w(g_coord["x0"], g_coord["y0"])
        g_coord["x1"], g_coord["y1"] = c_to_w(g_coord["x1"], g_coord["y1"])
    else:
        raise RuntimeError(f"project_to: invalid transition {src} -> {dst}")

    g_coord["coord-type"] = dst


# ============================================================
# GEOMETRY OPS
# ============================================================

def slide_pt(dx, dy):
    """
    Translate point registers by (dx, dy) in current coord space.
    """
    g_coord["x"] += dx
    g_coord["y"] += dy


def slide_rect(dx, dy):
    """
    Translate rect registers by (dx, dy) in current coord space.
    """
    g_coord["x0"] += dx
    g_coord["y0"] += dy
    g_coord["x1"] += dx
    g_coord["y1"] += dy


def explode_pt(size):
    """
    Convert point register into rect register centered on point.
    """
    x = g_coord["x"]
    y = g_coord["y"]
    g_coord["x0"] = x - size
    g_coord["y0"] = y - size
    g_coord["x1"] = x + size
    g_coord["y1"] = y + size


# ============================================================
# STACK OPS
# ============================================================

def push_pt():
    S.append((g_coord["x"], g_coord["y"], g_coord.get("coord-type")))


def pop_pt():
    if not S:
        raise RuntimeError("pop_pt: stack empty")

    x, y, coord_type = S.pop()
    g_coord["x"] = x
    g_coord["y"] = y
    g_coord["coord-type"] = coord_type


def push_rect():
    S.append((
        g_coord["x0"],
        g_coord["y0"],
        g_coord["x1"],
        g_coord["y1"],
        g_coord.get("coord-type"),
    ))


def pop_rect():
    if not S:
        raise RuntimeError("pop_rect: stack empty")

    x0, y0, x1, y1, coord_type = S.pop()
    g_coord["x0"] = x0
    g_coord["y0"] = y0
    g_coord["x1"] = x1
    g_coord["y1"] = y1
    g_coord["coord-type"] = coord_type


# ============================================================
# CONVENIENCE
# ============================================================

def get_xy():
    return (g_coord["x"], g_coord["y"])


def get_xyxy():
    return (g_coord["x0"], g_coord["y0"], g_coord["x1"], g_coord["y1"])
