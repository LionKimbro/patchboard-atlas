"""
Router communication for Patchboard Atlas.

Sends FileTalk messages to the Patchboard Router inbox.
"""

import json
import time
import uuid
from pathlib import Path

import lionscliapp as app

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import router_poll


def send_link(from_eid, from_channel, to_eid, to_channel):
    """Write a FileTalk link message to the router inbox."""
    router_inbox = app.ctx.get("path.router.inbox")
    if not router_inbox:
        return
    from_card = ecs.cmp_card_ref.get(from_eid)
    to_card = ecs.cmp_card_ref.get(to_eid)
    if from_card is None or to_card is None:
        return
    msg = {
        "channel": "link",
        "signal": {
            "source-folder": from_card["outbox"],
            "source-channel": from_channel,
            "destination-folder": to_card["inbox"],
            "destination-channel": to_channel,
        },
        "timestamp": str(time.time()),
    }
    filename = f"atlas-link-{uuid.uuid4().hex}.json"
    (Path(router_inbox) / filename).write_text(json.dumps(msg), encoding="utf-8")
    router_poll.enter_fast_mode()


def send_unlink(from_eid, from_channel, to_eid, to_channel):
    """Write a FileTalk unlink message to the router inbox."""
    router_inbox = app.ctx.get("path.router.inbox")
    if not router_inbox:
        return
    from_card = ecs.cmp_card_ref.get(from_eid)
    to_card = ecs.cmp_card_ref.get(to_eid)
    if from_card is None or to_card is None:
        return
    msg = {
        "channel": "unlink",
        "signal": {
            "source-folder": from_card["outbox"],
            "source-channel": from_channel,
            "destination-folder": to_card["inbox"],
            "destination-channel": to_channel,
        },
        "timestamp": str(time.time()),
    }
    filename = f"atlas-unlink-{uuid.uuid4().hex}.json"
    (Path(router_inbox) / filename).write_text(json.dumps(msg), encoding="utf-8")
    router_poll.enter_fast_mode()
