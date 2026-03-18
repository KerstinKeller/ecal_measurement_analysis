from __future__ import annotations

from dataclasses import dataclass
from math import fabs
from statistics import median
from typing import Iterable

from .analysis import ChannelDropSummary, DropEvent


@dataclass(frozen=True)
class PeriodicLossPattern:
    channel: str
    interval_ns: int
    interval_consistency: float
    event_count: int


@dataclass(frozen=True)
class DropBurst:
    channel: str
    start_ns: int
    end_ns: int
    event_count: int
    missing_count: int


@dataclass(frozen=True)
class ChannelCluster:
    channels: list[str]
    average_overlap_ratio: float


def _event_starts(summary: ChannelDropSummary) -> list[int]:
    return [event.start_ns for event in sorted(summary.drop_events, key=lambda item: item.start_ns)]


def detect_periodic_losses(
    summary: ChannelDropSummary,
    *,
    min_events: int = 3,
    tolerance_ratio: float = 0.2,
) -> PeriodicLossPattern | None:
    starts = _event_starts(summary)
    if len(starts) < min_events:
        return None

    intervals = [current - previous for previous, current in zip(starts, starts[1:])]
    if not intervals:
        return None

    baseline = max(int(median(intervals)), 1)
    deviations = [fabs(interval - baseline) / baseline for interval in intervals]
    consistency = 1.0 - min(sum(deviations) / len(deviations), 1.0)

    if any(delta > tolerance_ratio for delta in deviations):
        return None

    return PeriodicLossPattern(
        channel=summary.channel,
        interval_ns=baseline,
        interval_consistency=consistency,
        event_count=len(starts),
    )


def detect_drop_bursts(
    summary: ChannelDropSummary,
    *,
    max_separation_ns: int = 0,
) -> list[DropBurst]:
    events = sorted(summary.drop_events, key=lambda item: item.start_ns)
    if not events:
        return []

    bursts: list[list[DropEvent]] = [[events[0]]]
    for event in events[1:]:
        gap = event.start_ns - bursts[-1][-1].end_ns
        if gap <= max_separation_ns:
            bursts[-1].append(event)
        else:
            bursts.append([event])

    return [
        DropBurst(
            channel=summary.channel,
            start_ns=burst[0].start_ns,
            end_ns=burst[-1].end_ns,
            event_count=len(burst),
            missing_count=sum(event.missing_count for event in burst),
        )
        for burst in bursts
    ]


def cluster_channels_by_overlap(
    channel_summaries: Iterable[ChannelDropSummary],
    *,
    min_overlap_ratio: float = 0.3,
) -> list[ChannelCluster]:
    summaries = list(channel_summaries)
    if not summaries:
        return []

    intervals = {
        summary.channel: {(event.start_ns, event.end_ns) for event in summary.drop_events}
        for summary in summaries
    }
    channels = [summary.channel for summary in summaries]

    adjacency: dict[str, set[str]] = {channel: {channel} for channel in channels}
    for i, left in enumerate(channels):
        for right in channels[i + 1 :]:
            left_set = intervals[left]
            right_set = intervals[right]
            if not left_set and not right_set:
                continue

            intersection = len(left_set & right_set)
            union = len(left_set | right_set)
            ratio = 0.0 if union == 0 else intersection / union
            if ratio >= min_overlap_ratio:
                adjacency[left].add(right)
                adjacency[right].add(left)

    clusters: list[ChannelCluster] = []
    visited: set[str] = set()
    for channel in channels:
        if channel in visited:
            continue

        stack = [channel]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(adjacency[node] - component)

        visited |= component

        if len(component) == 1:
            overlap = 1.0 if intervals[next(iter(component))] else 0.0
            clusters.append(ChannelCluster(channels=sorted(component), average_overlap_ratio=overlap))
            continue

        ratios: list[float] = []
        sorted_component = sorted(component)
        for i, left in enumerate(sorted_component):
            for right in sorted_component[i + 1 :]:
                union = len(intervals[left] | intervals[right])
                intersect = len(intervals[left] & intervals[right])
                ratios.append(0.0 if union == 0 else intersect / union)

        clusters.append(
            ChannelCluster(
                channels=sorted_component,
                average_overlap_ratio=0.0 if not ratios else sum(ratios) / len(ratios),
            )
        )

    return sorted(clusters, key=lambda item: (-len(item.channels), item.channels))
