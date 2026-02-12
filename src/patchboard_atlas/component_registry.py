"""
Component ID Card registry for Patchboard Atlas.

Persistence cache of imported Component ID Cards.
Cards are keyed by canonical inbox path.
"""

import json
import os
from pathlib import Path

from patchboard_atlas import mem
from patchboard_atlas import paths
from patchboard_atlas import ecs_world as ecs


loaded_component_id_cards = {}


def validate_card():
    """( card -- card )  Castle-gate validation for top-of-stack card.

    Returns (True, None) if valid, (False, reason) if not.
    Card remains on stack.
    """
    card = mem.top()

    if not isinstance(card, dict):
        return (False, "card is not a dict")

    if card.get("schema_version") != 1:
        return (False, "schema_version must equal 1")

    inbox = card.get("inbox")
    if not isinstance(inbox, str) or not inbox:
        return (False, "inbox must be a non-empty string")
    if not os.path.isabs(inbox):
        return (False, "inbox must be an absolute path")

    outbox = card.get("outbox")
    if not isinstance(outbox, str) or not outbox:
        return (False, "outbox must be a non-empty string")
    if not os.path.isabs(outbox):
        return (False, "outbox must be an absolute path")

    if "title" not in card or not isinstance(card["title"], str):
        return (False, "title must be a string")

    channels = card.get("channels")
    if not isinstance(channels, dict):
        return (False, "channels must be a dict")

    ch_in = channels.get("in")
    if not isinstance(ch_in, list):
        return (False, "channels.in must be a list")
    for name in ch_in:
        if not isinstance(name, str):
            return (False, "channels.in entries must be strings")
    if len(ch_in) != len(set(ch_in)):
        return (False, "channels.in contains duplicate names")

    ch_out = channels.get("out")
    if not isinstance(ch_out, list):
        return (False, "channels.out must be a list")
    for name in ch_out:
        if not isinstance(name, str):
            return (False, "channels.out entries must be strings")
    if len(ch_out) != len(set(ch_out)):
        return (False, "channels.out contains duplicate names")

    return (True, None)


def canonical_inbox_key(inbox_path):
    """Normalize an inbox path to a canonical key."""
    return os.path.normcase(os.path.abspath(inbox_path))


def _persist_filename(key):
    """Derive a safe filename from a canonical inbox key."""
    sanitized = key.replace("\\", "_").replace("/", "_").replace(":", "_")
    return sanitized + ".json"


def find_entity_by_inbox(inbox_key):
    """Return eid for inbox_key, or None."""
    for eid, card in ecs.cmp_card_ref.items():
        if canonical_inbox_key(card["inbox"]) == inbox_key:
            return eid
    return None


def ingest_card():
    """( card -- card )  Validate and insert top-of-stack card into registry.

    If inbox key already exists, removes the old ECS entity first,
    then replaces the registry entry.
    Returns (True, canonical_key) or (False, reason).
    Card remains on stack for subsequent pipeline steps.
    """
    card = mem.top()
    ok, reason = validate_card()
    if not ok:
        return (False, reason)
    key = canonical_inbox_key(card["inbox"])
    old_eid = find_entity_by_inbox(key)
    if old_eid is not None:
        ecs.remove_entity(old_eid)
    loaded_component_id_cards[key] = card
    return (True, key)


def ingest_card_from_file(filepath):
    """( -- card )  Read JSON file, push card, validate, and ingest.

    Returns (True, canonical_key) or (False, reason).
    On success, card remains on stack. On failure, stack is unchanged.
    """
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except (OSError, IOError) as exc:
        return (False, f"cannot read file: {exc}")
    try:
        card = json.loads(text)
    except json.JSONDecodeError as exc:
        return (False, f"invalid JSON: {exc}")
    mem.push(card)
    ok, result = ingest_card()
    if not ok:
        mem.drop()
        return (False, result)
    return (True, result)


def ingest_cards_from_folder(dirpath):
    """( -- )  Enumerate *.json in dirpath, ingest each, create ECS entities.

    For each valid card: ingest, persist, allocate ECS entity, pop from stack.
    Returns (ok_count, fail_count).
    """
    ok_count = 0
    fail_count = 0
    folder = Path(dirpath)
    for path in sorted(folder.glob("*.json")):
        ok, _ = ingest_card_from_file(path)
        if ok:
            persist_card()
            eid = ecs.allocate_entity()
            ecs.cmp_card_ref[eid] = mem.pop()
            ok_count += 1
        else:
            fail_count += 1
    return (ok_count, fail_count)


def persist_card():
    """( card -- card )  Write top-of-stack card to persistence directory.

    Card remains on stack.
    """
    card = mem.top()
    persist_dir = paths.component_id_cards_dir()
    persist_dir.mkdir(parents=True, exist_ok=True)
    key = canonical_inbox_key(card["inbox"])
    filepath = persist_dir / _persist_filename(key)
    filepath.write_text(json.dumps(card, indent=2), encoding="utf-8")


def load_persisted_cards():
    """( -- )  Load all persisted card files into registry and create ECS entities.

    Invalid files are skipped. Returns (ok_count, fail_count).
    """
    persist_dir = paths.component_id_cards_dir()
    if not persist_dir.is_dir():
        return (0, 0)
    return ingest_cards_from_folder(persist_dir)


def delete_persisted_card(key):
    """Remove the persisted card file for a canonical inbox key."""
    persist_dir = paths.component_id_cards_dir()
    filepath = persist_dir / _persist_filename(key)
    if filepath.exists():
        filepath.unlink()


def validate_or_cull_persisted_cards():
    """Check all loaded cards for valid inbox/outbox folders on disk.

    Cards whose inbox or outbox folder no longer exists are removed
    from loaded_component_id_cards, deleted from disk persistence,
    and their ECS entities are removed. Each removal is logged.
    Called once at startup after load_persisted_cards().
    """
    from patchboard_atlas import log

    keys_to_remove = []
    for key, card in loaded_component_id_cards.items():
        if not os.path.isdir(card["inbox"]) or not os.path.isdir(card["outbox"]):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        card = loaded_component_id_cards[key]
        log.log("startup", f"Culling card: inbox/outbox not found: {card['title']}", "w")
        log.attach_context({"inbox": card["inbox"], "outbox": card["outbox"]})

        eid = find_entity_by_inbox(key)
        if eid is not None:
            ecs.remove_entity(eid)

        delete_persisted_card(key)
        del loaded_component_id_cards[key]


def clear_registry():
    """Empty loaded_component_id_cards."""
    loaded_component_id_cards.clear()
