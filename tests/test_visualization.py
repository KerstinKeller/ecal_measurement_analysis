from __future__ import annotations

from pathlib import Path

import pytest

from ecal_measurement_analysis.analysis import ChannelDropSummary, DropEvent
from ecal_measurement_analysis.visualization import plot_channel_drop_heatmap, plot_drop_timeline

try:
    import matplotlib  # noqa: F401

    HAS_MATPLOTLIB = True
except ModuleNotFoundError:
    HAS_MATPLOTLIB = False


@pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib not installed")
def test_plot_functions_create_output_files(tmp_path: Path) -> None:
    summaries = [
        ChannelDropSummary(
            channel="cam",
            total_samples=3,
            expected_samples=5,
            lost_samples=2,
            loss_ratio=0.4,
            drop_events=[DropEvent(channel="cam", start_ns=100, end_ns=250, missing_count=2)],
        )
    ]

    timeline = tmp_path / "timeline.png"
    heatmap = tmp_path / "heatmap.png"

    plot_drop_timeline(summaries, timeline)
    plot_channel_drop_heatmap(summaries, heatmap)

    assert timeline.exists()
    assert heatmap.exists()
    assert timeline.stat().st_size > 0
    assert heatmap.stat().st_size > 0
