from ecal_measurement_analysis.analysis import (
    ChannelDropSummary,
    DropEvent,
    MessageSample,
    analyze_channel,
    aggregate_drop_windows,
)


def test_analyze_channel_detects_drop_intervals_and_loss_ratio() -> None:
    samples = [
        MessageSample(channel="cam", timestamp_ns=0, sequence=1),
        MessageSample(channel="cam", timestamp_ns=100_000_000, sequence=2),
        MessageSample(channel="cam", timestamp_ns=400_000_000, sequence=5),
        MessageSample(channel="cam", timestamp_ns=500_000_000, sequence=6),
    ]

    summary = analyze_channel(samples)

    assert summary.channel == "cam"
    assert summary.total_samples == 4
    assert summary.expected_samples == 6
    assert summary.lost_samples == 2
    assert round(summary.loss_ratio, 3) == 0.333
    assert summary.drop_events == [
        DropEvent(channel="cam", start_ns=200_000_000, end_ns=300_000_000, missing_count=2)
    ]


def test_aggregate_drop_windows_flags_cross_channel_drop_overlap() -> None:
    summaries = [
        ChannelDropSummary(
            channel="cam",
            total_samples=5,
            expected_samples=7,
            lost_samples=2,
            loss_ratio=2 / 7,
            drop_events=[
                DropEvent(channel="cam", start_ns=100, end_ns=300, missing_count=2),
            ],
        ),
        ChannelDropSummary(
            channel="lidar",
            total_samples=4,
            expected_samples=6,
            lost_samples=2,
            loss_ratio=2 / 6,
            drop_events=[
                DropEvent(channel="lidar", start_ns=250, end_ns=450, missing_count=2),
            ],
        ),
        ChannelDropSummary(
            channel="imu",
            total_samples=6,
            expected_samples=6,
            lost_samples=0,
            loss_ratio=0.0,
            drop_events=[],
        ),
    ]

    windows = aggregate_drop_windows(summaries)

    assert windows == [
        {
            "start_ns": 100,
            "end_ns": 450,
            "channels": ["cam", "lidar"],
            "channel_count": 2,
        }
    ]


def test_analyze_channel_empty_input() -> None:
    summary = analyze_channel([])

    assert summary.channel == "<unknown>"
    assert summary.total_samples == 0
    assert summary.expected_samples == 0
    assert summary.lost_samples == 0
    assert summary.loss_ratio == 0.0
    assert summary.drop_events == []
