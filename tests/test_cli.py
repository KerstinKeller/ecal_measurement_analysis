from __future__ import annotations

import json
from pathlib import Path

import pytest

from ecal_measurement_analysis.analysis import ChannelDropSummary, DropEvent
from ecal_measurement_analysis.cli import main
from ecal_measurement_analysis.ecal_adapter import EcalMessageSample


def _sample_summary() -> list[ChannelDropSummary]:
    return [
        ChannelDropSummary(
            channel="cam",
            total_samples=3,
            expected_samples=5,
            lost_samples=2,
            loss_ratio=0.4,
            drop_events=[DropEvent(channel="cam", start_ns=100, end_ns=200, missing_count=2)],
        )
    ]


def test_extract_command_writes_csv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "entries.csv"
    monkeypatch.setattr(
        "ecal_measurement_analysis.cli.load_measurement_entries",
        lambda *args, **kwargs: [
            EcalMessageSample(channel="cam", snd_timestamp_ns=10, rcv_timestamp_ns=11, sequence=1)
        ],
    )

    rc = main(["extract", "/tmp/measurement", "--output", str(output), "--format", "csv"])

    assert rc == 0
    assert output.exists()


def test_analyze_command_writes_summary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    monkeypatch.setattr("ecal_measurement_analysis.cli.analyze_measurement", lambda *args, **kwargs: _sample_summary())

    rc = main(["analyze", "/tmp/measurement", "--output", str(output)])

    assert rc == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["totals"]["lost_samples"] == 2


def test_report_command_writes_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("ecal_measurement_analysis.cli.analyze_measurement", lambda *args, **kwargs: _sample_summary())

    def _fake_plot(_summaries, output_path):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text("plot", encoding="utf-8")

    monkeypatch.setattr("ecal_measurement_analysis.cli.plot_drop_timeline", _fake_plot)
    monkeypatch.setattr("ecal_measurement_analysis.cli.plot_channel_drop_heatmap", _fake_plot)

    rc = main(["report", "/tmp/measurement", "--output-dir", str(tmp_path)])

    assert rc == 0
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "timeline.png").exists()
    assert (tmp_path / "heatmap.png").exists()
