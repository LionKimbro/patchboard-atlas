"""
Centralized path calculations for Patchboard Atlas.

All paths derived from the lionscliapp execution root.
"""

import lionscliapp as app


def project_dir():
    """Return the .patchboard-atlas project directory."""
    return app.execroot.get_execroot() / ".patchboard-atlas"


def component_id_cards_dir():
    """Return the persistence directory for Component ID Cards."""
    return project_dir() / "component-id-cards"
