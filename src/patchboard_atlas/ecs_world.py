"""
ECS identity layer for Patchboard Atlas.

Module-level state for entity identity, card references, and spatial placement.
Spatial placement is optional; entities may exist without it.
"""


g = {
    "next_entity_id": 1,
}

cmp_entities = set()

cmp_card_ref = {}

cmp_spatial = {}


def allocate_entity():
    """
    Allocate a new ECS entity ID.

    Increments g["next_entity_id"], adds the new ID to cmp_entities,
    and returns it.
    """
    eid = g["next_entity_id"]
    g["next_entity_id"] += 1
    cmp_entities.add(eid)
    return eid


def remove_entity(eid):
    """
    Remove an entity from all ECS tables.

    Removes from cmp_entities, cmp_card_ref, and cmp_spatial (if present).
    """
    cmp_entities.discard(eid)
    cmp_card_ref.pop(eid, None)
    cmp_spatial.pop(eid, None)


def reset_ecs():
    """Reset all ECS state to initial empty condition."""
    g["next_entity_id"] = 1
    cmp_entities.clear()
    cmp_card_ref.clear()
    cmp_spatial.clear()
