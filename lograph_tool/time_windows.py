"""
Time Window Adjustment (TWA) - Paper Section 3.2

Segments temporal edge events into fixed time windows to capture evolving
microservice interactions. Each window represents a distinct temporal period,
enabling the model to learn sequential, time-dependent relationships.

Paper Reference: Eq. 4
    Tw = {Twj | Twj = {(f(si), f(di), ti, Ai) ∈ Tmap | ti ∈ wj}}
    where W = {w1, w2, ..., wn} represents fixed time intervals
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .otel_ingest import EdgeEvent


@dataclass(frozen=True)
class TimeWindow:
    """Represents a fixed time interval with metadata."""
    window_id: int
    start_ms: float
    end_ms: float

    def contains(self, timestamp: float) -> bool:
        """Check if timestamp falls within this window."""
        return self.start_ms <= timestamp < self.end_ms

    def duration_ms(self) -> float:
        """Get window duration in milliseconds."""
        return self.end_ms - self.start_ms


@dataclass(frozen=True)
class TimeWindowedEvents:
    """Events grouped by time window."""
    window: TimeWindow
    events: List[EdgeEvent]


def create_fixed_windows(
    min_timestamp: float,
    max_timestamp: float,
    window_size_ms: float = 100.0,
) -> List[TimeWindow]:
    """
    Create fixed time windows covering [min_timestamp, max_timestamp).

    Args:
        min_timestamp: Start time in ms (Unix time or relative)
        max_timestamp: End time in ms
        window_size_ms: Duration of each window in milliseconds (default: 100ms)

    Returns:
        List of TimeWindow objects in chronological order.

    Example:
        >>> windows = create_fixed_windows(0, 1000, window_size_ms=100)
        >>> len(windows)
        10
        >>> windows[0].start_ms
        0
        >>> windows[0].end_ms
        100
    """
    if max_timestamp <= min_timestamp:
        return []

    if window_size_ms <= 0:
        raise ValueError(f"window_size_ms must be positive, got {window_size_ms}")

    windows: List[TimeWindow] = []
    window_id = 0
    current_start = min_timestamp

    while current_start < max_timestamp:
        current_end = min(current_start + window_size_ms, max_timestamp)
        windows.append(
            TimeWindow(
                window_id=window_id,
                start_ms=current_start,
                end_ms=current_end,
            )
        )
        window_id += 1
        current_start = current_end

    return windows


def segment_events_by_windows(
    events: Sequence[EdgeEvent],
    windows: Sequence[TimeWindow],
) -> List[TimeWindowedEvents]:
    """
    Assign events to their corresponding time windows.

    Paper: Ensures events in Twj satisfy ti ∈ wj (timestamp within window)

    Args:
        events: List of EdgeEvent objects with timestamps
        windows: List of TimeWindow objects

    Returns:
        List of TimeWindowedEvents, one per window (may be empty for sparse data)
    """
    if not windows:
        return []

    # Group events by window
    windowed: Dict[int, List[EdgeEvent]] = {w.window_id: [] for w in windows}

    for event in events:
        for window in windows:
            if window.contains(event.timestamp):
                windowed[window.window_id].append(event)
                break  # Each event belongs to exactly one window

    # Create TimeWindowedEvents objects
    result: List[TimeWindowedEvents] = []
    for window in windows:
        window_events = windowed[window.window_id]
        result.append(TimeWindowedEvents(window=window, events=window_events))

    return result


def split_train_test_windows(
    windowed_events: Sequence[TimeWindowedEvents],
    train_cutoff_ms: float,
) -> Tuple[List[TimeWindowedEvents], List[TimeWindowedEvents]]:
    """
    Split windows into train and test sets based on timestamp cutoff.

    Paper Reference: Training uses timestamps 0-7000ms, testing 7000-10000ms

    Args:
        windowed_events: List of TimeWindowedEvents
        train_cutoff_ms: Timestamp threshold (windows with max_ts < cutoff go to train)

    Returns:
        (train_windows, test_windows) tuple
    """
    train_windows: List[TimeWindowedEvents] = []
    test_windows: List[TimeWindowedEvents] = []

    for windowed in windowed_events:
        if windowed.window.end_ms <= train_cutoff_ms:
            train_windows.append(windowed)
        else:
            test_windows.append(windowed)

    return train_windows, test_windows


def get_window_statistics(windowed_events: Sequence[TimeWindowedEvents]) -> Dict[str, float]:
    """
    Compute aggregate statistics across all windows.

    Returns:
        Dict with keys: total_windows, total_events, avg_events_per_window,
        min_events, max_events, total_unique_edges
    """
    total_windows = len(windowed_events)
    total_events = sum(len(w.events) for w in windowed_events)
    event_counts = [len(w.events) for w in windowed_events]

    # Count unique (source, target) pairs
    unique_edges = set()
    for windowed in windowed_events:
        for event in windowed.events:
            unique_edges.add((event.source, event.target))

    return {
        "total_windows": float(total_windows),
        "total_events": float(total_events),
        "avg_events_per_window": (
            float(total_events / total_windows) if total_windows > 0 else 0.0
        ),
        "min_events_in_window": float(min(event_counts)) if event_counts else 0.0,
        "max_events_in_window": float(max(event_counts)) if event_counts else 0.0,
        "total_unique_edges": float(len(unique_edges)),
    }
