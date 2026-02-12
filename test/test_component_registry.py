import json

import pytest
import lionscliapp as app

from patchboard_atlas import mem
from patchboard_atlas import ecs_world as ecs
from patchboard_atlas import component_registry as reg
from patchboard_atlas.reset import reset


VALID_CARD = {
    "schema_version": 1,
    "title": "Test Component",
    "inbox": "C:\\test\\inbox",
    "outbox": "C:\\test\\outbox",
    "channels": {
        "in": ["data", "control"],
        "out": ["result"],
    },
}

VALID_CARD_B = {
    "schema_version": 1,
    "title": "Other Component",
    "inbox": "C:\\other\\inbox",
    "outbox": "C:\\other\\outbox",
    "channels": {
        "in": ["input"],
        "out": ["output"],
    },
}


@pytest.fixture(autouse=True)
def clean_state(tmp_path):
    reset()
    app.reset()
    app.declare_app("test", "0.1")
    app.declare_projectdir(".patchboard-atlas")
    app.execroot.set_execroot(tmp_path)


# --- validate_card ---

def test_validate_valid_card():
    mem.push(VALID_CARD)
    ok, reason = reg.validate_card()
    assert ok is True
    assert reason is None
    mem.drop()


def test_validate_bad_schema_version():
    mem.push({**VALID_CARD, "schema_version": 2})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "schema_version" in reason
    mem.drop()


def test_validate_missing_inbox():
    card = {k: v for k, v in VALID_CARD.items() if k != "inbox"}
    mem.push(card)
    ok, reason = reg.validate_card()
    assert ok is False
    assert "inbox" in reason
    mem.drop()


def test_validate_relative_inbox():
    mem.push({**VALID_CARD, "inbox": "relative/path"})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "absolute" in reason
    mem.drop()


def test_validate_missing_outbox():
    card = {k: v for k, v in VALID_CARD.items() if k != "outbox"}
    mem.push(card)
    ok, reason = reg.validate_card()
    assert ok is False
    assert "outbox" in reason
    mem.drop()


def test_validate_relative_outbox():
    mem.push({**VALID_CARD, "outbox": "relative/path"})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "absolute" in reason
    mem.drop()


def test_validate_missing_title():
    card = {k: v for k, v in VALID_CARD.items() if k != "title"}
    mem.push(card)
    ok, reason = reg.validate_card()
    assert ok is False
    assert "title" in reason
    mem.drop()


def test_validate_channels_not_dict():
    mem.push({**VALID_CARD, "channels": "bad"})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "channels" in reason
    mem.drop()


def test_validate_channels_in_not_list():
    mem.push({**VALID_CARD, "channels": {"in": "bad", "out": []}})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "channels.in" in reason
    mem.drop()


def test_validate_channels_out_not_list():
    mem.push({**VALID_CARD, "channels": {"in": [], "out": "bad"}})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "channels.out" in reason
    mem.drop()


def test_validate_duplicate_channel_in():
    mem.push({**VALID_CARD, "channels": {"in": ["a", "a"], "out": []}})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "duplicate" in reason
    mem.drop()


def test_validate_duplicate_channel_out():
    mem.push({**VALID_CARD, "channels": {"in": [], "out": ["x", "x"]}})
    ok, reason = reg.validate_card()
    assert ok is False
    assert "duplicate" in reason
    mem.drop()


def test_validate_not_a_dict():
    mem.push("not a dict")
    ok, reason = reg.validate_card()
    assert ok is False
    mem.drop()


# --- ingest_card ---

def test_ingest_card_inserts_into_registry():
    mem.push(VALID_CARD)
    ok, key = reg.ingest_card()
    assert ok is True
    assert key in reg.loaded_component_id_cards
    assert reg.loaded_component_id_cards[key] is VALID_CARD
    mem.drop()


def test_ingest_card_leaves_card_on_stack():
    mem.push(VALID_CARD)
    reg.ingest_card()
    assert mem.top() is VALID_CARD
    mem.drop()


def test_ingest_invalid_card_returns_false():
    mem.push({"bad": "card"})
    ok, reason = reg.ingest_card()
    assert ok is False
    assert isinstance(reason, str)
    mem.drop()


def test_ingest_duplicate_inbox_removes_old_ecs_entity():
    mem.push(VALID_CARD)
    reg.ingest_card()
    eid_old = ecs.allocate_entity()
    ecs.cmp_card_ref[eid_old] = mem.pop()

    updated_card = {**VALID_CARD, "title": "Updated Title"}
    mem.push(updated_card)
    reg.ingest_card()
    mem.drop()

    assert eid_old not in ecs.cmp_entities
    assert eid_old not in ecs.cmp_card_ref


# --- find_entity_by_inbox ---

def test_find_entity_by_inbox_found():
    mem.push(VALID_CARD)
    reg.ingest_card()
    eid = ecs.allocate_entity()
    ecs.cmp_card_ref[eid] = mem.pop()

    key = reg.canonical_inbox_key(VALID_CARD["inbox"])
    assert reg.find_entity_by_inbox(key) == eid


def test_find_entity_by_inbox_not_found():
    assert reg.find_entity_by_inbox("C:\\nonexistent") is None


# --- ingest_card_from_file ---

def test_ingest_card_from_file_valid(tmp_path):
    filepath = tmp_path / "card.json"
    filepath.write_text(json.dumps(VALID_CARD), encoding="utf-8")
    ok, key = reg.ingest_card_from_file(filepath)
    assert ok is True
    assert key in reg.loaded_component_id_cards
    assert mem.top()["title"] == "Test Component"
    mem.drop()


def test_ingest_card_from_file_invalid_json(tmp_path):
    filepath = tmp_path / "bad.json"
    filepath.write_text("{not valid json", encoding="utf-8")
    ok, reason = reg.ingest_card_from_file(filepath)
    assert ok is False
    assert "JSON" in reason
    assert len(mem.S) == 0


def test_ingest_card_from_file_schema_invalid(tmp_path):
    filepath = tmp_path / "bad_schema.json"
    filepath.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    ok, reason = reg.ingest_card_from_file(filepath)
    assert ok is False
    assert len(mem.S) == 0


def test_ingest_card_from_file_missing_file():
    ok, reason = reg.ingest_card_from_file("C:\\nonexistent\\file.json")
    assert ok is False
    assert "cannot read" in reason


# --- ingest_cards_from_folder ---

def test_ingest_cards_from_folder(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(VALID_CARD), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(VALID_CARD_B), encoding="utf-8")
    (tmp_path / "bad.json").write_text("{bad", encoding="utf-8")

    ok_count, fail_count = reg.ingest_cards_from_folder(tmp_path)
    assert ok_count == 2
    assert fail_count == 1
    assert len(ecs.cmp_entities) == 2
    assert len(ecs.cmp_card_ref) == 2
    assert len(mem.S) == 0


# --- persistence ---

def test_persist_card_writes_file():
    mem.push(VALID_CARD)
    reg.persist_card()
    persist_dir = reg.paths.component_id_cards_dir()
    files = list(persist_dir.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["title"] == "Test Component"
    mem.drop()


def test_load_persisted_cards():
    mem.push(VALID_CARD)
    reg.persist_card()
    mem.drop()
    reg.clear_registry()
    ecs.reset_ecs()

    ok_count, fail_count = reg.load_persisted_cards()
    assert ok_count == 1
    assert fail_count == 0
    assert len(reg.loaded_component_id_cards) == 1
    assert len(ecs.cmp_entities) == 1


def test_load_persisted_cards_empty_dir():
    ok_count, fail_count = reg.load_persisted_cards()
    assert ok_count == 0
    assert fail_count == 0


def test_delete_persisted_card():
    mem.push(VALID_CARD)
    reg.persist_card()
    mem.drop()
    key = reg.canonical_inbox_key(VALID_CARD["inbox"])
    reg.delete_persisted_card(key)
    persist_dir = reg.paths.component_id_cards_dir()
    assert list(persist_dir.glob("*.json")) == []


# --- clear_registry ---

def test_clear_registry():
    mem.push(VALID_CARD)
    reg.ingest_card()
    mem.drop()
    reg.clear_registry()
    assert reg.loaded_component_id_cards == {}
