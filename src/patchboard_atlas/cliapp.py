"""
Patchboard Atlas CLI entrypoint (lionscliapp).
"""

import sys
from pathlib import Path

import lionscliapp as app
from tkintertester import harness

from patchboard_atlas import gui_scaffold


def run():
    """
    Default command (no subcommand).
    """
    flags = ""

    if app.ctx["runtime.testing"]:
        gui_scaffold.g["quit-on-close"] = False
        register_tests()
        flags += "x"

    harness.run_host(app_entry, flags)

    if app.ctx["runtime.testing"]:
        harness.print_results()


def app_entry():
    """
    Create the GUI application instance.
    """
    gui_scaffold.create_gui(harness.g["root"])


def app_reset():
    """
    Tear down the GUI application instance between tests.
    """
    gui_scaffold.destroy_gui()


def register_tests():
    """
    Register GUI tests with tkintertester.
    """
    search_roots = []
    search_roots.append(Path.cwd().resolve())
    search_roots.extend(Path.cwd().resolve().parents)
    search_roots.append(Path(__file__).resolve().parents[3])

    for root in search_roots:
        if (root / "guitest").is_dir():
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            break

    from guitest.gui_scaffold_tests import register_gui_scaffold_tests

    register_gui_scaffold_tests()


def main():
    """
    Declare CLI structure and enter lionscliapp lifecycle.
    """
    app.declare_app("patchboard-atlas", "0.1.0")
    app.describe_app("Patchboard Atlas CLI")
    app.declare_projectdir(".patchboard-atlas")

    app.declare_key("path.router.inbox", None)
    app.declare_key("path.router.outbox", None)
    app.declare_key("runtime.testing", False)

    app.declare_cmd("", run)

    harness.set_resetfn(app_reset)

    app.main()
