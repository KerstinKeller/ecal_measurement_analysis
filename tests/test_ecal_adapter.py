from __future__ import annotations

import pytest

from ecal_measurement_analysis.ecal_adapter import (
    EcalMeasurementError,
    EcalMessageSample,
    analyze_measurement,
    compute_latency_ns,
    load_measurement_entries,
    load_measurement_samples,
)


class _FakeReader:
    def __init__(self, entries_by_channel: dict[str, list[dict[str, int]]], ok: bool = True):
        self._entries_by_channel = entries_by_channel
        self._ok = ok
        self.closed = False

    def is_ok(self) -> bool:
        return self._ok

    def get_channel_names(self) -> list[str]:
        return list(self._entries_by_channel.keys())

    def get_entries_info(self, channel: str) -> list[dict[str, int]]:
        return self._entries_by_channel[channel]

    def close(self) -> None:
        self.closed = True


class _FakeHdf5Module:
    def __init__(self, reader: _FakeReader):
        self._reader = reader

    def Meas(self, path: str, access: int) -> _FakeReader:  # noqa: N802
        del path, access
        return self._reader


def test_load_measurement_entries_keeps_send_and_receive_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = _FakeReader(
        {
            "cam": [
                {"snd_timestamp": 90, "rcv_timestamp": 100, "counter": 10},
                {"snd_timestamp": 180, "rcv_timestamp": 200, "counter": 11},
            ],
            "imu": [{"snd_timestamp": 110, "rcv_timestamp": 120, "counter": 1}],
        }
    )

    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FakeHdf5Module(reader),
    )

    entries = load_measurement_entries("/tmp/measurement", channels=["cam"])

    assert entries == [
        EcalMessageSample(channel="cam", snd_timestamp_ns=90, rcv_timestamp_ns=100, sequence=10),
        EcalMessageSample(channel="cam", snd_timestamp_ns=180, rcv_timestamp_ns=200, sequence=11),
    ]
    assert reader.closed


def test_load_measurement_samples_selects_snd_or_rcv_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = _FakeReader(
        {
            "cam": [
                {"snd_timestamp": 90, "rcv_timestamp": 100, "counter": 1},
                {"snd_timestamp": 190, "rcv_timestamp": 200, "counter": 2},
            ]
        }
    )
    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FakeHdf5Module(reader),
    )

    rcv_samples = load_measurement_samples("/tmp/measurement", timestamp_field="rcv_timestamp")
    snd_samples = load_measurement_samples("/tmp/measurement", timestamp_field="snd_timestamp")

    assert [sample.timestamp_ns for sample in rcv_samples] == [100, 200]
    assert [sample.timestamp_ns for sample in snd_samples] == [90, 190]


def test_load_measurement_samples_falls_back_to_index_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = _FakeReader(
        {
            "cam": [
                {"snd_timestamp": 90, "rcv_timestamp": 100},
                {"snd_timestamp": 190, "rcv_timestamp": 200},
                {"snd_timestamp": 390, "rcv_timestamp": 400},
            ]
        }
    )
    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FakeHdf5Module(reader),
    )

    samples = load_measurement_samples("/tmp/measurement")

    assert [sample.sequence for sample in samples] == [1, 2, 3]


def test_load_measurement_samples_raises_on_invalid_measurement(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = _FakeReader({}, ok=False)
    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FakeHdf5Module(reader),
    )

    with pytest.raises(EcalMeasurementError, match="Failed to open"):
        load_measurement_samples("/tmp/missing")


def test_load_measurement_samples_rejects_unknown_timestamp_basis() -> None:
    with pytest.raises(ValueError, match="timestamp_field"):
        load_measurement_samples("/tmp/measurement", timestamp_field="foo")


def test_compute_latency_ns() -> None:
    entries = [
        EcalMessageSample(channel="cam", snd_timestamp_ns=80, rcv_timestamp_ns=100, sequence=1),
        EcalMessageSample(channel="cam", snd_timestamp_ns=180, rcv_timestamp_ns=200, sequence=2),
    ]

    assert compute_latency_ns(entries) == [20, 20]


def test_analyze_measurement_runs_drop_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = _FakeReader(
        {
            "cam": [
                {"snd_timestamp": 0, "rcv_timestamp": 0, "counter": 1},
                {"snd_timestamp": 100, "rcv_timestamp": 100, "counter": 2},
                {"snd_timestamp": 400, "rcv_timestamp": 400, "counter": 5},
            ]
        }
    )
    monkeypatch.setattr(
        "ecal_measurement_analysis.ecal_adapter._import_hdf5_module",
        lambda: _FakeHdf5Module(reader),
    )

    summaries = analyze_measurement("/tmp/measurement")

    assert len(summaries) == 1
    assert summaries[0].channel == "cam"
    assert summaries[0].lost_samples == 2
    assert summaries[0].drop_events[0].start_ns == 200
    assert summaries[0].drop_events[0].end_ns == 300
