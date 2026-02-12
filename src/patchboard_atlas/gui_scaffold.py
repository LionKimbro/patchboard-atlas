"""
Tkinter GUI scaffold for Patchboard Atlas.

This module builds a structural shell only.
"""

import tkinter as tk
from tkinter import ttk, filedialog


colors = {
    "bg": "#1e1e1e",
    "pane-bg": "#2a2a2a",
    "button-bg": "#333333",
    "foreground": "#e6e6e6",
    "error": "#ff6b6b",
    "red": "#ff6b6b",
    "success": "#6bff95",
    "green": "#6bff95",
    "info": "#6bb7ff",
    "blue": "#6bb7ff"
}

FOREGROUND = "FOREGROUND"  # semantics: default
RED = "RED"  # semantics: "error" or "alert"
GREEN = "GREEN"  # semantics: "success" or "definitional"
BLUE = "BLUE"  # semantics: "info" or "structure"

status_colors = {
    FOREGROUND: "foreground",
    RED: "red",
    GREEN: "green",
    BLUE: "blue",
}

g = {
    "gui-created": False,
    "status-color": FOREGROUND,
    "quit-on-close": True,
}


# Widget registry — structural scaffold.
# All widgets are registered here so that the GUI structure
# is visible statically while reading the file.
# Values are populated at runtime.

widgets = {

    # --- roots ---
    "root": None,
    "main-window": None,
    "console-window": None,

    # --- layout spine ---
    "panes": None,

    # --- menu bar ---
    "menu-bar": None,
    "file-menu": None,

    # --- left tree pane ---
    "tree-pane": None,
    "component-tree": None,

    # --- canvas pane ---
    "canvas-pane": None,
    "canvas": None,
    "canvas-y-scroll": None,
    "canvas-x-scroll": None,

    # --- inspector pane ---
    "inspector-pane": None,
    "inspector-label": None,

    # --- status bar ---
    "status-frame": None,
    "status-label": None,

    # --- button bar ---
    "button-frame": None,
    "console-button": None,

    # --- console window contents ---
    "console-output": None,
    "console-input": None,
}


sv = {}


def create_gui(root):
    """
    Create the Patchboard Atlas scaffold inside a new Toplevel.
    """
    if g.get("gui-created"):
        destroy_gui()

    widgets["root"] = root

    def on_main_window_close():
        destroy_gui()
        if g["quit-on-close"]:
            root.quit()

    main_window = tk.Toplevel(root)
    main_window.title("Patchboard Atlas")
    main_window.configure(bg=colors["bg"])
    main_window.resizable(True, True)
    main_window.protocol("WM_DELETE_WINDOW", on_main_window_close)
    widgets["main-window"] = main_window

    style = ttk.Style()
    style.configure("Scaffold.TFrame", background=colors["bg"])
    style.configure("Pane.TFrame", background=colors["pane-bg"])
    style.configure("Scaffold.TLabel", background=colors["pane-bg"], foreground=colors["foreground"])
    style.configure("Status.TFrame", background=colors["bg"])
    style.configure("ButtonBar.TFrame", background=colors["bg"])
    style.configure("Tree.Treeview",
                    background=colors["pane-bg"],
                    foreground=colors["foreground"],
                    fieldbackground=colors["pane-bg"])

    # --- Menu bar ---
    menu_bar = tk.Menu(main_window, tearoff=0)
    widgets["menu-bar"] = menu_bar

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Import Card...", underline=0,
                          command=cmd_import_component_id_card_file)
    file_menu.add_command(label="Import Card Folder...", underline=12,
                          command=cmd_import_component_id_card_folder)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", underline=1, command=cmd_exit)
    widgets["file-menu"] = file_menu

    menu_bar.add_cascade(label="File", menu=file_menu)
    main_window.configure(menu=menu_bar)

    main_window.columnconfigure(0, weight=1)
    main_window.rowconfigure(0, weight=1)

    main_frame = ttk.Frame(main_window, style="Scaffold.TFrame")
    main_frame.grid(row=0, column=0, sticky="nsew")
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(0, weight=1)

    # --- Main pane row (horizontal split) ---
    panes = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
    panes.grid(row=0, column=0, sticky="nsew")
    widgets["panes"] = panes

    tree_pane = ttk.Frame(panes, style="Pane.TFrame", width=200)
    tree_pane.grid_propagate(False)
    tree_pane.columnconfigure(0, weight=1)
    tree_pane.rowconfigure(0, weight=1)
    widgets["tree-pane"] = tree_pane

    component_tree = ttk.Treeview(
        tree_pane,
        columns=("eid", "inbox", "outbox"),
        show="tree",
        style="Tree.Treeview",
    )
    component_tree.grid(row=0, column=0, sticky="nsew")
    widgets["component-tree"] = component_tree

    canvas_pane = ttk.Frame(panes, style="Pane.TFrame")
    canvas_pane.columnconfigure(0, weight=1)
    canvas_pane.rowconfigure(0, weight=1)
    widgets["canvas-pane"] = canvas_pane

    canvas = tk.Canvas(canvas_pane, background="#dddddd", highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    widgets["canvas"] = canvas

    y_scroll = ttk.Scrollbar(canvas_pane, orient=tk.VERTICAL, command=canvas.yview)
    y_scroll.grid(row=0, column=1, sticky="ns")
    widgets["canvas-y-scroll"] = y_scroll

    x_scroll = ttk.Scrollbar(canvas_pane, orient=tk.HORIZONTAL, command=canvas.xview)
    x_scroll.grid(row=1, column=0, sticky="ew")
    widgets["canvas-x-scroll"] = x_scroll

    canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    inspector_pane = ttk.Frame(panes, style="Pane.TFrame", width=250)
    inspector_pane.grid_propagate(False)
    widgets["inspector-pane"] = inspector_pane

    inspector_label = ttk.Label(inspector_pane, text="Inspector (placeholder)", style="Scaffold.TLabel")
    inspector_label.grid(row=0, column=0, sticky="nw", padx=8, pady=8)
    widgets["inspector-label"] = inspector_label

    panes.add(tree_pane, weight=0)
    panes.add(canvas_pane, weight=1)
    panes.add(inspector_pane, weight=0)

    # --- Status bar ---
    status_frame = ttk.Frame(main_frame, style="Status.TFrame")
    status_frame.grid(row=1, column=0, sticky="ew")
    status_frame.columnconfigure(0, weight=1)
    widgets["status-frame"] = status_frame

    sv["status-text"] = tk.StringVar(value="Ready.")
    status_label = tk.Label(
        status_frame,
        textvariable=sv["status-text"],
        bg=colors["bg"],
        fg=colors[status_colors[g["status-color"]]],
        anchor="w",
        padx=8,
        pady=4,
    )
    status_label.grid(row=0, column=0, sticky="ew")
    widgets["status-label"] = status_label

    # --- Button bar ---
    button_frame = ttk.Frame(main_frame, style="ButtonBar.TFrame")
    button_frame.grid(row=2, column=0, sticky="ew")
    button_frame.columnconfigure(0, weight=1)
    widgets["button-frame"] = button_frame

    console_btn = ttk.Button(button_frame, text="Console", command=open_console_window)
    console_btn.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    widgets["console-button"] = console_btn

    g["gui-created"] = True


def destroy_gui():
    """
    Destroy all windows and clear widget references.
    """
    console_window = widgets.get("console-window")
    if console_window is not None and console_window.winfo_exists():
        console_window.destroy()

    main_window = widgets.get("main-window")
    if main_window is not None and main_window.winfo_exists():
        main_window.destroy()

    widgets.clear()
    sv.clear()
    g["gui-created"] = False
    g["status-color"] = FOREGROUND


def open_console_window():
    """
    Create or raise the console window.
    """
    if not g.get("gui-created"):
        return

    console_window = widgets.get("console-window")
    if console_window is not None and console_window.winfo_exists():
        console_window.deiconify()
        console_window.lift()
        return

    root = widgets.get("root")
    console_window = tk.Toplevel(root)
    console_window.title("Patchboard Atlas Console")
    console_window.configure(bg=colors["bg"])
    console_window.resizable(True, True)
    widgets["console-window"] = console_window

    console_window.columnconfigure(0, weight=1)
    console_window.rowconfigure(0, weight=1)

    output = tk.Text(console_window, bg="#0b1220", fg=colors["foreground"], wrap="word")
    output.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    widgets["console-output"] = output

    input_entry = tk.Entry(console_window, bg=colors["bg"], fg=colors["foreground"])
    input_entry.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
    widgets["console-input"] = input_entry


def set_status(message, color):
    """
    Update the status bar message and color.
    """
    sv["status-text"].set(message)
    g["status-color"] = color
    status_label = widgets.get("status-label")
    if status_label is not None and status_label.winfo_exists():
        key = status_colors[color]
        status_label.configure(fg=colors[key])


def cmd_import_component_id_card_file():
    """File > Import Card... menu command."""
    from patchboard_atlas import mem
    from patchboard_atlas import ecs_world as ecs
    from patchboard_atlas import component_registry as reg
    from patchboard_atlas import tree_projection as tp

    filepath = filedialog.askopenfilename(
        title="Import Component ID Card",
        filetypes=[("JSON files", "*.json")],
    )
    if not filepath:
        return

    ok, result = reg.ingest_card_from_file(filepath)
    if not ok:
        set_status(result, RED)
        return

    reg.persist_card()
    eid = ecs.allocate_entity()
    ecs.cmp_card_ref[eid] = mem.pop()
    tp.rebuild_tree()
    set_status(f"Imported: {filepath}", GREEN)


def cmd_import_component_id_card_folder():
    """File > Import Card Folder... menu command."""
    from patchboard_atlas import mem
    from patchboard_atlas import ecs_world as ecs
    from patchboard_atlas import component_registry as reg
    from patchboard_atlas import tree_projection as tp

    dirpath = filedialog.askdirectory(title="Import Component ID Card Folder")
    if not dirpath:
        return

    ok_count, fail_count = reg.ingest_cards_from_folder(dirpath)
    tp.rebuild_tree()
    if fail_count == 0:
        set_status(f"Imported {ok_count} card(s).", GREEN)
    else:
        set_status(f"Imported {ok_count}, failed {fail_count}.", RED)


def cmd_exit():
    """File > Exit menu command."""
    root = widgets.get("root")
    if root is not None:
        destroy_gui()
        if g["quit-on-close"]:
            root.quit()
