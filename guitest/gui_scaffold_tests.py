from tkintertester import harness

from patchboard_atlas import gui_scaffold


def register_gui_scaffold_tests():
    harness.add_test(
        "gui scaffold presence",
        [
            step_check_main_widgets,
        ],
    )

    harness.add_test(
        "gui scaffold console open/close",
        [
            step_open_console,
            step_check_console_widgets,
            step_close_console,
        ],
    )

    harness.add_test(
        "gui scaffold status",
        [
            step_set_status_foreground,
            step_set_status_red,
            step_check_status_text,
            step_check_status_color_red,
        ],
    )


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


def step_set_status_foreground():
    gui_scaffold.set_status("Ready.", gui_scaffold.FOREGROUND)
    return ("next", None)


def step_set_status_red():
    gui_scaffold.set_status("Problem.", gui_scaffold.RED)
    return ("next", None)


def step_check_status_text():
    text_var = gui_scaffold.sv.get("status-text")
    if text_var is None:
        return ("fail", "missing status-text StringVar")
    if text_var.get() != "Problem.":
        return ("fail", "status text mismatch")
    return ("next", None)


def step_check_status_color_red():
    label = gui_scaffold.widgets.get("status-label")
    if label is None or not label.winfo_exists():
        return ("fail", "missing status-label")
    if label.cget("fg") != gui_scaffold.colors["error"]:
        return ("fail", "status label color mismatch")
    return ("next", None)
