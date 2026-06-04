"""Event catalogue: every name has a builder; payloads round-trip through the bus."""
from __future__ import annotations

import asyncio

from core import events


def test_every_event_has_builder():
    for name in events.ALL_EVENTS:
        assert name in events.BUILDERS, f"{name} missing a builder"


def test_event_names_upper_snake():
    for name in events.ALL_EVENTS:
        assert name.isupper() and " " not in name


def test_builders_return_dicts_with_timestamp():
    assert events.make_fact_created("f1", "src")["fact_id"] == "f1"
    assert "timestamp" in events.make_esm_transition("f1", "Observed", "Validated")
    assert events.make_chat_turn("q", ["f1", "f2"])["trace_fact_ids"] == ["f1", "f2"]


def test_payload_round_trips_through_event_bus():
    from core.event_bus import EventBus

    bus = EventBus()
    seen = []

    async def handler(evt):
        seen.append(evt)

    async def run():
        bus.subscribe(events.FACT_CREATED, handler)
        await bus.publish(
            {"type": events.FACT_CREATED, "source": "test",
             "payload": events.make_fact_created("f1", "unit")},
            dispatch=True,
        )

    asyncio.run(run())
    assert seen and seen[0]["payload"]["fact_id"] == "f1"
