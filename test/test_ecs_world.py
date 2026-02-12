import pytest

from patchboard_atlas import ecs_world as ecs
from patchboard_atlas.reset import reset


@pytest.fixture(autouse=True)
def clean_state():
    reset()


def test_initial_state():
    assert ecs.g["next_entity_id"] == 1
    assert ecs.cmp_entities == set()
    assert ecs.cmp_card_ref == {}
    assert ecs.cmp_spatial == {}


def test_allocate_entity_returns_incrementing_ids():
    eid1 = ecs.allocate_entity()
    eid2 = ecs.allocate_entity()
    eid3 = ecs.allocate_entity()
    assert eid1 == 1
    assert eid2 == 2
    assert eid3 == 3


def test_allocate_entity_adds_to_cmp_entities():
    eid = ecs.allocate_entity()
    assert eid in ecs.cmp_entities


def test_allocate_entity_advances_counter():
    ecs.allocate_entity()
    ecs.allocate_entity()
    assert ecs.g["next_entity_id"] == 3


def test_remove_entity_clears_from_cmp_entities():
    eid = ecs.allocate_entity()
    ecs.remove_entity(eid)
    assert eid not in ecs.cmp_entities


def test_remove_entity_clears_from_cmp_card_ref():
    eid = ecs.allocate_entity()
    ecs.cmp_card_ref[eid] = {"title": "Test"}
    ecs.remove_entity(eid)
    assert eid not in ecs.cmp_card_ref


def test_remove_entity_clears_from_cmp_spatial():
    eid = ecs.allocate_entity()
    ecs.cmp_spatial[eid] = {"x": 0, "y": 0, "width": 100, "height": 50}
    ecs.remove_entity(eid)
    assert eid not in ecs.cmp_spatial


def test_remove_entity_tolerates_missing_card_ref_and_spatial():
    eid = ecs.allocate_entity()
    ecs.remove_entity(eid)
    assert eid not in ecs.cmp_entities


def test_remove_entity_tolerates_unknown_eid():
    ecs.remove_entity(999)
    assert 999 not in ecs.cmp_entities


def test_reset_ecs_clears_all_state():
    eid1 = ecs.allocate_entity()
    eid2 = ecs.allocate_entity()
    ecs.cmp_card_ref[eid1] = {"title": "A"}
    ecs.cmp_spatial[eid2] = {"x": 0, "y": 0, "width": 10, "height": 10}
    ecs.reset_ecs()
    assert ecs.g["next_entity_id"] == 1
    assert ecs.cmp_entities == set()
    assert ecs.cmp_card_ref == {}
    assert ecs.cmp_spatial == {}
