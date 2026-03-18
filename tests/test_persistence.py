from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import pyarrow  # noqa: F401

    HAS_PYARROW = True
except ModuleNotFoundError:
    HAS_PYARROW = False

from ecal_measurement_analysis import analysis
from ecal_measurement_analysis.ecal_adapter import analyze_measurement, load_measurement_entries
from ecal_measurement_analysis.persistence import (
    read_ecal_entries_csv,
    read_ecal_entries_parquet,
    read_message_samples_csv,
    read_message_samples_parquet,
    write_ecal_entries_csv,
    write_ecal_entries_parquet,
    write_message_samples_csv,
    write_message_samples_parquet,
)


class _FixtureReader:
    def __init__(self, fixture_data: dict[str, list[dict[str, int]]], ok: bool = True):
        self._fixture_data = fixture_data
        self._ok = ok

    def is_ok(self) -> bool:
        return self._ok

    def get_channel_names(self) -> list[str]:
        return list(self._fixture_data.keys())

    def get_entries_info(self, channel: str) -> list[dict[str, int]]:
        return self._fixture_data[channel]

    def close(self) -> None:
        return None


class _FixtureHdf5Module:
    def __init__(self, fixture_data: dict[str, list[dict[str, int]]]):
        self._fixture_data = fixture_data

    def Meas(self, path: str, access: int) -> _FixtureReader:  # noqa: N802
        del path, access
        return _FixtureReader(self._fixture_data)


@pytest.fixture
def sample_fixture_data() -> dict[str, list[dict[str, int]]]:
    fixture_path = Path("tests/fixtures/sample_measurement_entries.json")
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_csv_round_trip_for_ecal_entries_and_message_samples(tmp_path: Path) -> None:
    entries = [
        analysis.MessageSample(channel="cam", timestamp_ns=100, sequence=1),
        analysis.MessageSample(channel="cam", timestamp_ns=200, sequence=2),
    ]

    message_csv = tmp_path / "samples.csv"
    write_message_samples_csv(entries, message_csv)
    assert read_message_samples_csv(message_csv) == entries


@pytest.mark.skipif(not HAS_PYARROW, reason="pyarrow not installed")
def test_parquet_round_trip_for_ecal_entries_and_message_samples(tmp_path: Path) -> None:
    from ecal_measurement_analysis.ecal_adapter import EcalMessageSample

    ecal_entries = [
        EcalMessageSample(channel="cam", snd_timestamp_ns=90, rcv_timestamp_ns=100, sequence=1),
        EcalMessageSample(channel="cam", snd_timestamp_ns=190, rcv_timestamp_ns=200, sequence=2),
    ]
    samples = [
        analysis.MessageSample(channel="cam", timestamp_ns=100, sequence=1),
        analysis.MessageSample(channel="cam", timestamp_ns=200, sequence=2),
    ]

    entry_parquet = tmp_path / "entries.parquet"
    sample_parquet = tmp_path / "samples.parquet"

    write_ecal_entries_parquet(ecal_entries, entry_parquet)
    write_message_samples_parquet(samples, sample_parquet)

    assert read_ecal_entries_parquet(entry_parquet) == ecal_entries
    assert read_message_samples_parquet(sample_parquet) == samples


def test_fixture_integration_extract_persist_and_analyze(
    monkeypatch: pytest.MonkeyPatch,
    sample_fixture_data: dict[str, list[dict[str, int]]],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FixtureHdf5Module(sample_fixture_data),
    )

    entries = load_measurement_entries("/tmp/fixture")
    entry_csv = tmp_path / "fixture_entries.csv"
    write_ecal_entries_csv(entries, entry_csv)
    persisted_entries = read_ecal_entries_csv(entry_csv)

    assert persisted_entries == entries

    summaries = analyze_measurement("/tmp/fixture")
    by_channel = {summary.channel: summary for summary in summaries}
    assert by_channel["cam"].lost_samples == 2
    assert by_channel["lidar"].lost_samples == 0
