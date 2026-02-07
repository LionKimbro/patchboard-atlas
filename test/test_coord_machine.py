import pytest

from patchboard_atlas import coord_machine as cm


def test_coord_reset_state_defaults():
    cm.coord_reset_state()
    assert cm.g_coord == {
        "x": 0,
        "y": 0,
        "x0": 0,
        "y0": 0,
        "x1": 0,
        "y1": 0,
        "coord-type": "w",
    }
    assert cm.g_cam == {
        "x": 0,
        "y": 0,
        "zoom-num": 1,
        "zoom-den": 1,
    }
    assert cm.g_view == {
        "canvas-view-w": 0,
        "canvas-view-h": 0,
    }
    assert cm.g_attachment == {"bbox": (0, 0, 0, 0)}
    assert cm.g_label == {"coord": (0, 0)}
    assert cm.g_event == {"x": 0, "y": 0}
    assert cm.S == []


def test_set_zoom_updates_camera_ratio():
    cm.coord_reset_state()
    cm.set_zoom(3, 2)
    assert cm.g_cam["zoom-num"] == 3
    assert cm.g_cam["zoom-den"] == 2


def test_set_viewport_updates_canvas_view():
    cm.coord_reset_state()
    cm.set_viewport(800, 600)
    assert cm.g_view["canvas-view-w"] == 800
    assert cm.g_view["canvas-view-h"] == 600


def test_set_xy_updates_point_registers():
    cm.coord_reset_state()
    cm.set_xy(5, -7)
    assert cm.g_coord["x"] == 5
    assert cm.g_coord["y"] == -7


def test_load_rect_from_attachment_sets_rect_and_world():
    cm.coord_reset_state()
    cm.g_attachment["bbox"] = (1, 2, 3, 4)
    cm.load_rect("attachment")
    assert cm.get_xyxy() == (1, 2, 3, 4)
    assert cm.g_coord["coord-type"] == "w"


def test_store_rect_to_attachment_requires_world():
    cm.coord_reset_state()
    cm.g_coord["coord-type"] = "c"
    with pytest.raises(RuntimeError):
        cm.store_rect("attachment")


def test_store_rect_to_attachment_writes_bbox():
    cm.coord_reset_state()
    cm.g_coord["x0"] = -1
    cm.g_coord["y0"] = -2
    cm.g_coord["x1"] = 10
    cm.g_coord["y1"] = 20
    cm.g_coord["coord-type"] = "w"
    cm.store_rect("attachment")
    assert cm.g_attachment["bbox"] == (-1, -2, 10, 20)


def test_load_pt_event_sets_canvas_and_coord_type():
    cm.coord_reset_state()
    cm.g_event["x"] = 11
    cm.g_event["y"] = 22
    cm.load_pt("event")
    assert cm.get_xy() == (11, 22)
    assert cm.g_coord["coord-type"] == "c"


def test_load_pt_center_reads_rect_center():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 9
    cm.g_coord["y1"] = 7
    cm.load_pt("center")
    assert cm.get_xy() == (4, 3)


def test_load_pt_center_south_reads_rect_bottom_center():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 10
    cm.g_coord["y1"] = 7
    cm.load_pt("center-south")
    assert cm.get_xy() == (5, 7)


def test_load_pt_corners_reads_rect_corners():
    cm.coord_reset_state()
    cm.g_coord["x0"] = -3
    cm.g_coord["y0"] = -4
    cm.g_coord["x1"] = 5
    cm.g_coord["y1"] = 6

    cm.load_pt("nw")
    assert cm.get_xy() == (-3, -4)
    cm.load_pt("ne")
    assert cm.get_xy() == (5, -4)
    cm.load_pt("se")
    assert cm.get_xy() == (5, 6)
    cm.load_pt("sw")
    assert cm.get_xy() == (-3, 6)


def test_load_pt_label_sets_world_and_coord_type():
    cm.coord_reset_state()
    cm.g_label["coord"] = (7, 8)
    cm.g_coord["coord-type"] = "c"
    cm.load_pt("label")
    assert cm.get_xy() == (7, 8)
    assert cm.g_coord["coord-type"] == "w"


def test_store_pt_corner_updates_rect_corner():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 10
    cm.g_coord["y1"] = 20
    cm.set_xy(3, 4)
    cm.store_pt("nw")
    assert cm.get_xyxy() == (3, 4, 10, 20)


def test_store_pt_center_moves_rect_to_point():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 10
    cm.g_coord["y1"] = 10
    cm.set_xy(7, 5)
    cm.store_pt("center")
    assert cm.get_xyxy() == (2, 0, 12, 10)


def test_store_pt_cam_updates_camera_position():
    cm.coord_reset_state()
    cm.set_xy(9, -3)
    cm.store_pt("cam")
    assert cm.g_cam["x"] == 9
    assert cm.g_cam["y"] == -3


def test_project_to_world_to_canvas_identity_zoom():
    cm.coord_reset_state()
    cm.set_viewport(100, 80)
    cm.set_zoom(1, 1)
    cm.set_xy(10, 20)
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 10
    cm.g_coord["y1"] = 20
    cm.g_coord["coord-type"] = "w"

    cm.project_to("c")
    assert cm.get_xy() == (10 + 50, 20 + 40)
    assert cm.get_xyxy() == (0 + 50, 0 + 40, 10 + 50, 20 + 40)


def test_project_to_canvas_to_world_identity_zoom():
    cm.coord_reset_state()
    cm.set_viewport(100, 80)
    cm.set_zoom(1, 1)
    cm.set_xy(60, 50)
    cm.g_coord["x0"] = 50
    cm.g_coord["y0"] = 40
    cm.g_coord["x1"] = 70
    cm.g_coord["y1"] = 60
    cm.g_coord["coord-type"] = "c"

    cm.project_to("w")
    assert cm.get_xy() == (10, 10)
    assert cm.get_xyxy() == (0, 0, 20, 20)


def test_project_to_world_to_canvas_with_camera_offset():
    cm.coord_reset_state()
    cm.set_viewport(200, 100)
    cm.set_zoom(1, 1)
    cm.set_xy(10, 20)
    cm.store_pt("cam")

    cm.set_xy(30, 40)
    cm.g_coord["x0"] = 20
    cm.g_coord["y0"] = 30
    cm.g_coord["x1"] = 40
    cm.g_coord["y1"] = 50
    cm.g_coord["coord-type"] = "w"

    cm.project_to("c")
    assert cm.get_xy() == (30 - 10 + 100, 40 - 20 + 50)


def test_project_to_canvas_to_world_with_camera_offset():
    cm.coord_reset_state()
    cm.set_viewport(200, 100)
    cm.set_zoom(1, 1)
    cm.set_xy(10, 20)
    cm.store_pt("cam")

    cm.set_xy(130, 80)
    cm.g_coord["x0"] = 120
    cm.g_coord["y0"] = 70
    cm.g_coord["x1"] = 140
    cm.g_coord["y1"] = 90
    cm.g_coord["coord-type"] = "c"

    cm.project_to("w")
    assert cm.get_xy() == (40, 50)


def test_project_to_world_to_canvas_with_zoom():
    cm.coord_reset_state()
    cm.set_viewport(100, 100)
    cm.set_zoom(2, 1)
    cm.set_xy(0, 0)
    cm.store_pt("cam")

    cm.set_xy(5, 5)
    cm.g_coord["x0"] = 0
    cm.g_coord["y0"] = 0
    cm.g_coord["x1"] = 5
    cm.g_coord["y1"] = 5
    cm.g_coord["coord-type"] = "w"

    cm.project_to("c")
    assert cm.get_xy() == (5 * 2 + 50, 5 * 2 + 50)
    assert cm.get_xyxy() == (0 + 50, 0 + 50, 10 + 50, 10 + 50)


def test_project_to_canvas_to_world_with_zoom():
    cm.coord_reset_state()
    cm.set_viewport(100, 100)
    cm.set_zoom(2, 1)
    cm.set_xy(0, 0)
    cm.store_pt("cam")

    cm.set_xy(60, 60)
    cm.g_coord["x0"] = 50
    cm.g_coord["y0"] = 50
    cm.g_coord["x1"] = 70
    cm.g_coord["y1"] = 70
    cm.g_coord["coord-type"] = "c"

    cm.project_to("w")
    assert cm.get_xy() == (5, 5)
    assert cm.get_xyxy() == (0, 0, 10, 10)


def test_project_round_trip_point_stability():
    cm.coord_reset_state()
    cm.set_viewport(801, 601)
    cm.set_zoom(3, 2)
    cm.set_xy(11, -7)
    cm.store_pt("cam")

    cm.set_xy(123, -57)
    cm.g_coord["coord-type"] = "w"
    cm.project_to("c")
    cm.project_to("w")

    x, y = cm.get_xy()
    assert abs(x - 123) <= 1
    assert abs(y + 57) <= 1


def test_project_round_trip_rect_stability():
    cm.coord_reset_state()
    cm.set_viewport(801, 601)
    cm.set_zoom(5, 3)
    cm.set_xy(7, 13)
    cm.store_pt("cam")

    cm.g_coord["x0"] = -22
    cm.g_coord["y0"] = 15
    cm.g_coord["x1"] = 79
    cm.g_coord["y1"] = 104
    cm.g_coord["coord-type"] = "w"
    cm.project_to("c")
    cm.project_to("w")

    x0, y0, x1, y1 = cm.get_xyxy()
    assert abs(x0 + 22) <= 1
    assert abs(y0 - 15) <= 1
    assert abs(x1 - 79) <= 1
    assert abs(y1 - 104) <= 1


def test_slide_pt_moves_point():
    cm.coord_reset_state()
    cm.set_xy(3, 4)
    cm.slide_pt(2, -5)
    assert cm.get_xy() == (5, -1)


def test_slide_rect_moves_rect():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 1
    cm.g_coord["y0"] = 2
    cm.g_coord["x1"] = 3
    cm.g_coord["y1"] = 4
    cm.slide_rect(-1, 5)
    assert cm.get_xyxy() == (0, 7, 2, 9)


def test_explode_pt_builds_rect_centered():
    cm.coord_reset_state()
    cm.set_xy(10, -10)
    cm.explode_pt(3)
    assert cm.get_xyxy() == (7, -13, 13, -7)


def test_push_pop_pt_restores_point_and_coord_type():
    cm.coord_reset_state()
    cm.set_xy(1, 2)
    cm.g_coord["coord-type"] = "w"
    cm.push_pt()
    cm.set_xy(9, 9)
    cm.g_coord["coord-type"] = "c"
    cm.pop_pt()
    assert cm.get_xy() == (1, 2)
    assert cm.g_coord["coord-type"] == "w"


def test_push_pop_rect_restores_rect_and_coord_type():
    cm.coord_reset_state()
    cm.g_coord["x0"] = 1
    cm.g_coord["y0"] = 2
    cm.g_coord["x1"] = 3
    cm.g_coord["y1"] = 4
    cm.g_coord["coord-type"] = "w"
    cm.push_rect()
    cm.g_coord["x0"] = 9
    cm.g_coord["y0"] = 8
    cm.g_coord["x1"] = 7
    cm.g_coord["y1"] = 6
    cm.g_coord["coord-type"] = "c"
    cm.pop_rect()
    assert cm.get_xyxy() == (1, 2, 3, 4)
    assert cm.g_coord["coord-type"] == "w"


def test_pop_pt_raises_on_empty_stack():
    cm.coord_reset_state()
    with pytest.raises(RuntimeError):
        cm.pop_pt()


def test_pop_rect_raises_on_empty_stack():
    cm.coord_reset_state()
    with pytest.raises(RuntimeError):
        cm.pop_rect()
