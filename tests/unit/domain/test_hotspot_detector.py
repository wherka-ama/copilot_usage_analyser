"""Unit tests for HotspotDetector."""

from datetime import datetime, timedelta
from uuid import uuid4

from src.copilot_usage_analyser.domain.entities import Event, EventType, TokenUsage
from src.copilot_usage_analyser.domain.services import HotspotDetector


def test_detect_high_token_usage():
    """Test detection of high token usage hotspots."""
    detector = HotspotDetector(threshold_std_dev=2.0)

    base_time = datetime.utcnow()
    events = []

    # Normal events
    for i in range(10):
        events.append(
            Event(
                event_id=uuid4(),
                timestamp=base_time + timedelta(seconds=i),
                event_type=EventType.MODEL_TURN,
                summary=f"Event {i}",
                token_usage=TokenUsage(input=100, output=50, cached=0),
                duration_ms=1000,
            )
        )

    # High token usage event
    events.append(
        Event(
            event_id=uuid4(),
            timestamp=base_time + timedelta(seconds=11),
            event_type=EventType.MODEL_TURN,
            summary="High token event",
            token_usage=TokenUsage(input=10000, output=5000, cached=0),
            duration_ms=2000,
            details={"model": "gpt-4"},
        )
    )

    hotspots = detector.detect_hotspots(events)

    # Should detect at least one hotspot for high token usage
    assert len(hotspots) > 0
    assert any(h.hotspot_type.value == "high_token_usage" for h in hotspots)


def test_detect_long_duration():
    """Test detection of long duration hotspots."""
    detector = HotspotDetector(threshold_std_dev=2.0)

    base_time = datetime.utcnow()
    events = []

    # Normal events
    for i in range(10):
        events.append(
            Event(
                event_id=uuid4(),
                timestamp=base_time + timedelta(seconds=i),
                event_type=EventType.TOOL_CALL,
                summary=f"Event {i}",
                token_usage=TokenUsage(input=0, output=0, cached=0),
                duration_ms=100,
            )
        )

    # Long duration event
    events.append(
        Event(
            event_id=uuid4(),
            timestamp=base_time + timedelta(seconds=11),
            event_type=EventType.TOOL_CALL,
            summary="Long duration event",
            token_usage=TokenUsage(input=0, output=0, cached=0),
            duration_ms=10000,
        )
    )

    hotspots = detector.detect_hotspots(events)

    # Should detect at least one hotspot for long duration
    assert len(hotspots) > 0
    assert any(h.hotspot_type.value == "long_duration" for h in hotspots)


def test_detect_frequent_failures():
    """Test detection of frequent failure patterns."""
    detector = HotspotDetector(threshold_std_dev=2.0)

    base_time = datetime.utcnow()
    events = []

    # Multiple errors with same pattern
    for i in range(5):
        events.append(
            Event(
                event_id=uuid4(),
                timestamp=base_time + timedelta(seconds=i),
                event_type=EventType.ERROR,
                summary="File not found",
                token_usage=TokenUsage(input=0, output=0, cached=0),
                duration_ms=0,
            )
        )

    hotspots = detector.detect_hotspots(events)

    # Should detect frequent failures
    assert len(hotspots) > 0
    assert any(h.hotspot_type.value == "frequent_failures" for h in hotspots)


def test_no_hotspots_for_normal_events():
    """Test that normal events don't trigger hotspots."""
    detector = HotspotDetector(threshold_std_dev=2.0)

    base_time = datetime.utcnow()
    events = []

    # All normal events
    for i in range(10):
        events.append(
            Event(
                event_id=uuid4(),
                timestamp=base_time + timedelta(seconds=i),
                event_type=EventType.MODEL_TURN,
                summary=f"Event {i}",
                token_usage=TokenUsage(input=100, output=50, cached=0),
                duration_ms=1000,
            )
        )

    hotspots = detector.detect_hotspots(events)

    # Should not detect any hotspots
    assert len(hotspots) == 0
