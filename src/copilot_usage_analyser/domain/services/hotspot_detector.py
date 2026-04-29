"""Hotspot detector service."""

from statistics import mean, stdev
from typing import List

from ..entities import Event, EventType, Hotspot, HotspotSeverity, HotspotType
from uuid import uuid4


class HotspotDetector:
    """Service for detecting usage hotspots."""

    def __init__(self, threshold_std_dev: float = 2.0):
        """Initialize with threshold for hotspot detection."""
        self.threshold = threshold_std_dev

    def detect_hotspots(self, events: List[Event]) -> List[Hotspot]:
        """Detect anomalous usage patterns."""
        hotspots = []

        # Detect high token usage
        token_hotspots = self._detect_high_token_usage(events)
        hotspots.extend(token_hotspots)

        # Detect long duration
        duration_hotspots = self._detect_long_duration(events)
        hotspots.extend(duration_hotspots)

        # Detect frequent failures
        failure_hotspots = self._detect_frequent_failures(events)
        hotspots.extend(failure_hotspots)

        return hotspots

    def _detect_high_token_usage(self, events: List[Event]) -> List[Hotspot]:
        """Detect events with anomalously high token usage."""
        token_counts = [e.token_usage.total for e in events if e.token_usage.total > 0]
        if len(token_counts) < 3:
            return []

        avg_tokens = mean(token_counts)
        try:
            std_tokens = stdev(token_counts)
        except:
            std_tokens = 0

        if std_tokens == 0:
            return []

        threshold = avg_tokens + (self.threshold * std_tokens)
        hotspots = []

        for event in events:
            if event.token_usage.total > threshold:
                severity = self._calculate_severity(event.token_usage.total, avg_tokens, std_tokens)
                hotspots.append(
                    Hotspot(
                        hotspot_id=uuid4(),
                        event_id=event.event_id,
                        hotspot_type=HotspotType.HIGH_TOKEN_USAGE,
                        severity=severity,
                        description=f"Event used {event.token_usage.total} tokens, significantly above average of {avg_tokens:.0f}",
                        token_count=event.token_usage.total,
                        task_description=event.summary,
                        model_used=event.details.get("model") if event.details else None,
                        timestamp=event.timestamp.isoformat(),
                    )
                )

        return hotspots

    def _detect_long_duration(self, events: List[Event]) -> List[Hotspot]:
        """Detect events with anomalously long duration."""
        durations = [e.duration_ms for e in events if e.duration_ms > 0]
        if len(durations) < 3:
            return []

        avg_duration = mean(durations)
        try:
            std_duration = stdev(durations)
        except:
            std_duration = 0

        if std_duration == 0:
            return []

        threshold = avg_duration + (self.threshold * std_duration)
        hotspots = []

        for event in events:
            if event.duration_ms > threshold:
                severity = self._calculate_severity(event.duration_ms, avg_duration, std_duration)
                hotspots.append(
                    Hotspot(
                        hotspot_id=uuid4(),
                        event_id=event.event_id,
                        hotspot_type=HotspotType.LONG_DURATION,
                        severity=severity,
                        description=f"Event took {event.duration_ms:.0f}ms, significantly above average of {avg_duration:.0f}ms",
                        duration_ms=event.duration_ms,
                        task_description=event.summary,
                        model_used=event.details.get("model") if event.details else None,
                        timestamp=event.timestamp.isoformat(),
                    )
                )

        return hotspots

    def _detect_frequent_failures(self, events: List[Event]) -> List[Hotspot]:
        """Detect patterns of frequent failures."""
        error_events = [e for e in events if e.event_type == EventType.ERROR]
        if len(error_events) < 2:
            return []

        # Group by task/pattern
        from collections import Counter

        error_patterns = Counter(e.summary for e in error_events)
        threshold = 2  # More than 2 errors with same pattern

        hotspots = []
        for pattern, count in error_patterns.items():
            if count >= threshold:
                severity = HotspotSeverity.HIGH if count >= 4 else HotspotSeverity.MEDIUM
                hotspots.append(
                    Hotspot(
                        hotspot_id=uuid4(),
                        event_id=error_events[0].event_id,  # First occurrence
                        hotspot_type=HotspotType.FREQUENT_FAILURES,
                        severity=severity,
                        description=f"Error pattern occurred {count} times: {pattern}",
                        failure_count=count,
                        task_description=pattern,
                        timestamp=error_events[0].timestamp.isoformat(),
                    )
                )

        return hotspots

    def _calculate_severity(self, value: float, avg: float, std: float) -> HotspotSeverity:
        """Calculate severity based on deviation from mean."""
        deviations = (value - avg) / std if std > 0 else 0
        if deviations >= 3 * self.threshold:
            return HotspotSeverity.HIGH
        elif deviations >= 2 * self.threshold:
            return HotspotSeverity.MEDIUM
        else:
            return HotspotSeverity.LOW
