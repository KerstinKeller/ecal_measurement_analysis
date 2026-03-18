from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .analysis import ChannelDropSummary, aggregate_drop_windows
from .pattern_analysis import (
    cluster_channels_by_overlap,
    detect_drop_bursts,
    detect_periodic_losses,
)


def build_summary_report(channel_summaries: Iterable[ChannelDropSummary]) -> dict[str, object]:
    summaries = list(channel_summaries)
    total_expected = sum(summary.expected_samples for summary in summaries)
    total_lost = sum(summary.lost_samples for summary in summaries)

    periodic_losses = [
        asdict(pattern)
        for summary in summaries
        for pattern in [detect_periodic_losses(summary)]
        if pattern is not None
    ]
    bursts = {summary.channel: [asdict(burst) for burst in detect_drop_bursts(summary)] for summary in summaries}
    clusters = [asdict(cluster) for cluster in cluster_channels_by_overlap(summaries)]

    return {
        "channels": [asdict(summary) for summary in summaries],
        "synchronized_windows": aggregate_drop_windows(summaries),
        "patterns": {
            "periodic_losses": periodic_losses,
            "bursts": bursts,
            "channel_clusters": clusters,
        },
        "totals": {
            "channel_count": len(summaries),
            "expected_samples": total_expected,
            "lost_samples": total_lost,
            "loss_ratio": 0.0 if total_expected == 0 else total_lost / total_expected,
        },
    }


def write_summary_report_json(
    channel_summaries: Iterable[ChannelDropSummary],
    output_path: str | Path,
) -> dict[str, object]:
    report = build_summary_report(channel_summaries)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
