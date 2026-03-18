from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MessageSample:
    channel: str
    timestamp_ns: int
    sequence: int


@dataclass(frozen=True)
class DropEvent:
    channel: str
    start_ns: int
    end_ns: int
    missing_count: int


@dataclass(frozen=True)
class ChannelDropSummary:
    channel: str
    total_samples: int
    expected_samples: int
    lost_samples: int
    loss_ratio: float
    drop_events: list[DropEvent]


def analyze_channel(samples: Iterable[MessageSample]) -> ChannelDropSummary:
    ordered = sorted(samples, key=lambda sample: sample.sequence)
    if not ordered:
        return ChannelDropSummary(
            channel="<unknown>",
            total_samples=0,
            expected_samples=0,
            lost_samples=0,
            loss_ratio=0.0,
            drop_events=[],
        )

    channel = ordered[0].channel
    total_samples = len(ordered)
    min_seq = ordered[0].sequence
    max_seq = ordered[-1].sequence
    expected_samples = max_seq - min_seq + 1
    lost_samples = max(expected_samples - total_samples, 0)

    drop_events: list[DropEvent] = []
    for previous, current in zip(ordered, ordered[1:]):
        gap = current.sequence - previous.sequence
        if gap <= 1:
            continue

        missing = gap - 1
        if missing == 1:
            estimated_period = current.timestamp_ns - previous.timestamp_ns
        else:
            estimated_period = (current.timestamp_ns - previous.timestamp_ns) // gap

        start_ns = previous.timestamp_ns + estimated_period
        end_ns = current.timestamp_ns - estimated_period
        drop_events.append(
            DropEvent(
                channel=channel,
                start_ns=start_ns,
                end_ns=end_ns,
                missing_count=missing,
            )
        )

    loss_ratio = 0.0 if expected_samples == 0 else lost_samples / expected_samples
    return ChannelDropSummary(
        channel=channel,
        total_samples=total_samples,
        expected_samples=expected_samples,
        lost_samples=lost_samples,
        loss_ratio=loss_ratio,
        drop_events=drop_events,
    )


def aggregate_drop_windows(
    channel_summaries: Iterable[ChannelDropSummary],
) -> list[dict[str, int | list[str]]]:
    intervals: list[dict[str, int | str]] = []
    for summary in channel_summaries:
        for event in summary.drop_events:
            intervals.append(
                {
                    "channel": summary.channel,
                    "start_ns": event.start_ns,
                    "end_ns": event.end_ns,
                }
            )

    if not intervals:
        return []

    intervals.sort(key=lambda item: int(item["start_ns"]))

    merged: list[dict[str, int | set[str]]] = []
    for interval in intervals:
        channel = str(interval["channel"])
        start_ns = int(interval["start_ns"])
        end_ns = int(interval["end_ns"])

        if not merged or start_ns > int(merged[-1]["end_ns"]):
            merged.append(
                {
                    "start_ns": start_ns,
                    "end_ns": end_ns,
                    "channels": {channel},
                }
            )
            continue

        merged[-1]["end_ns"] = max(int(merged[-1]["end_ns"]), end_ns)
        merged[-1]["channels"].add(channel)

    output: list[dict[str, int | list[str]]] = []
    for item in merged:
        channels = sorted(item["channels"])
        if len(channels) < 2:
            continue

        output.append(
            {
                "start_ns": int(item["start_ns"]),
                "end_ns": int(item["end_ns"]),
                "channels": channels,
                "channel_count": len(channels),
            }
        )
    return output
