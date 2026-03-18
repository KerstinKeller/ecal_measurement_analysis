from __future__ import annotations

import json
from pathlib import Path

from ecal_measurement_analysis.analysis import ChannelDropSummary, DropEvent
from ecal_measurement_analysis.reporting import build_summary_report, write_summary_report_json


def _sample_summaries() -> list[ChannelDropSummary]:
    return [
        ChannelDropSummary(
            channel="cam",
            total_samples=3,
            expected_samples=5,
            lost_samples=2,
            loss_ratio=0.4,
            drop_events=[DropEvent(channel="cam", start_ns=100, end_ns=200, missing_count=2)],
        ),
        ChannelDropSummary(
            channel="lidar",
            total_samples=4,
            expected_samples=4,
            lost_samples=0,
            loss_ratio=0.0,
            drop_events=[],
        ),
    ]


def test_build_summary_report_contains_totals_and_windows() -> None:
    report = build_summary_report(_sample_summaries())

    assert report["totals"]["channel_count"] == 2
    assert report["totals"]["expected_samples"] == 9
    assert report["totals"]["lost_samples"] == 2
    assert report["synchronized_windows"] == []
    assert "patterns" in report
    assert "periodic_losses" in report["patterns"]
    assert "bursts" in report["patterns"]
    assert "channel_clusters" in report["patterns"]


def test_write_summary_report_json(tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    report = write_summary_report_json(_sample_summaries(), output)

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == report
