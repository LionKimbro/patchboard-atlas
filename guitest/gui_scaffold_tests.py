from tkintertester import harness

from patchboard_atlas import gui_scaffold


def register_gui_scaffold_tests():
    harness.add_test(
        "gui scaffold create/open/close/destroy",
        [
            step_create_gui,
            step_check_main_widgets,
            step_open_console,
            step_check_console_widgets,
            step_close_console,
            step_destroy_gui,
            step_check_destroyed,
        ],
    )


def step_create_gui():
    gui_scaffold.create_gui(harness.g["root"])
    return ("next", None)


def step_check_main_widgets():
    required = [
        "main-window",
        "panes",
        "tree-pane",
        "canvas-pane",
        "inspector-pane",
        "canvas",
        "status-label",
        "button-frame",
        "console-button",
    ]
    for key in required:
        w = gui_scaffold.widgets.get(key)
        if w is None or not w.winfo_exists():
            return ("fail", f"missing widget: {key}")
    return ("next", None)


def step_open_console():
    gui_scaffold.open_console_window()
    return ("next", 10)


def step_check_console_widgets():
    required = [
        "console-window",
        "console-output",
        "console-input",
    ]
    for key in required:
        w = gui_scaffold.widgets.get(key)
        if w is None or not w.winfo_exists():
            return ("fail", f"missing console widget: {key}")
    return ("next", None)


def step_close_console():
    console_window = gui_scaffold.widgets.get("console-window")
    if console_window is not None and console_window.winfo_exists():
        console_window.destroy()
    return ("next", None)


def step_destroy_gui():
    gui_scaffold.destroy_gui()
    return ("next", None)


def step_check_destroyed():
    main_window = gui_scaffold.widgets.get("main-window")
    if main_window is not None and main_window.winfo_exists():
        return ("fail", "main-window still exists after destroy")
    return ("success", None)
