import pytest

from patchboard_atlas import log
from patchboard_atlas.reset import reset


@pytest.fixture(autouse=True)
def clean_state():
    reset()


def test_log_info_appends_record():
    log.log("startup", "system ready")
    assert len(log.g_log) == 1
    rec = log.g_log[0]
    assert rec["level"] == "info"
    assert rec["category"] == "startup"
    assert rec["message"] == "system ready"
    assert "timestamp" in rec


def test_log_warning():
    log.log("validation", "missing field", "w")
    assert log.g_log[0]["level"] == "warning"


def test_log_error():
    log.log("ingestion", "bad json", "e")
    assert log.g_log[0]["level"] == "error"


def test_log_default_flag_is_info():
    log.log("test", "hello")
    assert log.g_log[0]["level"] == "info"


def test_log_invalid_flag_raises():
    with pytest.raises(KeyError):
        log.log("test", "hello", "z")


def test_log_appends_multiple():
    log.log("a", "first")
    log.log("b", "second")
    log.log("c", "third")
    assert len(log.g_log) == 3
    assert log.g_log[0]["message"] == "first"
    assert log.g_log[2]["message"] == "third"


def test_attach_context_adds_to_last_record():
    log.log("startup", "loaded card")
    log.attach_context({"inbox": "/tmp/inbox", "title": "Test"})
    rec = log.g_log[0]
    assert rec["context"]["inbox"] == "/tmp/inbox"
    assert rec["context"]["title"] == "Test"


def test_attach_context_targets_last_record():
    log.log("a", "first")
    log.log("b", "second")
    log.attach_context({"key": "value"})
    assert "context" not in log.g_log[0]
    assert log.g_log[1]["context"]["key"] == "value"


def test_clear_log_empties_buffer():
    log.log("a", "one")
    log.log("b", "two")
    log.clear_log()
    assert log.g_log == []


def test_timestamp_is_utc_iso8601():
    log.log("test", "check timestamp")
    ts = log.g_log[0]["timestamp"]
    assert "T" in ts
    assert ts.endswith("+00:00")
