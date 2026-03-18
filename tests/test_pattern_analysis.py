from __future__ import annotations

from ecal_measurement_analysis.analysis import ChannelDropSummary, DropEvent
from ecal_measurement_analysis.pattern_analysis import (
    cluster_channels_by_overlap,
    detect_drop_bursts,
    detect_periodic_losses,
)


def test_detect_periodic_losses_returns_pattern_for_regular_intervals() -> None:
    summary = ChannelDropSummary(
        channel="cam",
        total_samples=8,
        expected_samples=12,
        lost_samples=4,
        loss_ratio=4 / 12,
        drop_events=[
            DropEvent(channel="cam", start_ns=100, end_ns=110, missing_count=1),
            DropEvent(channel="cam", start_ns=200, end_ns=210, missing_count=1),
            DropEvent(channel="cam", start_ns=300, end_ns=310, missing_count=1),
            DropEvent(channel="cam", start_ns=400, end_ns=410, missing_count=1),
        ],
    )

    pattern = detect_periodic_losses(summary, min_events=3, tolerance_ratio=0.15)

    assert pattern is not None
    assert pattern.interval_ns == 100
    assert pattern.channel == "cam"


def test_detect_drop_bursts_groups_nearby_events() -> None:
    summary = ChannelDropSummary(
        channel="lidar",
        total_samples=8,
        expected_samples=12,
        lost_samples=4,
        loss_ratio=4 / 12,
        drop_events=[
            DropEvent(channel="lidar", start_ns=100, end_ns=120, missing_count=1),
            DropEvent(channel="lidar", start_ns=125, end_ns=130, missing_count=2),
            DropEvent(channel="lidar", start_ns=300, end_ns=310, missing_count=1),
        ],
    )

    bursts = detect_drop_bursts(summary, max_separation_ns=10)

    assert len(bursts) == 2
    assert bursts[0].event_count == 2
    assert bursts[0].missing_count == 3
    assert bursts[1].event_count == 1


def test_cluster_channels_by_overlap_builds_components() -> None:
    summaries = [
        ChannelDropSummary(
            channel="cam",
            total_samples=5,
            expected_samples=7,
            lost_samples=2,
            loss_ratio=2 / 7,
            drop_events=[DropEvent(channel="cam", start_ns=100, end_ns=120, missing_count=1)],
        ),
        ChannelDropSummary(
            channel="imu",
            total_samples=5,
            expected_samples=7,
            lost_samples=2,
            loss_ratio=2 / 7,
            drop_events=[DropEvent(channel="imu", start_ns=100, end_ns=120, missing_count=1)],
        ),
        ChannelDropSummary(
            channel="gps",
            total_samples=7,
            expected_samples=7,
            lost_samples=0,
            loss_ratio=0.0,
            drop_events=[],
        ),
    ]

    clusters = cluster_channels_by_overlap(summaries, min_overlap_ratio=0.5)

    assert clusters[0].channels == ["cam", "imu"]
    assert any(cluster.channels == ["gps"] for cluster in clusters)
