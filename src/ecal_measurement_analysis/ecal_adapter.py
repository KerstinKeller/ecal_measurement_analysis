from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from importlib import import_module
from typing import Iterable

from .analysis import ChannelDropSummary, MessageSample, analyze_channel


class EcalDependencyError(ImportError):
    """Raised when eclipse-ecal bindings are not installed."""


class EcalMeasurementError(RuntimeError):
    """Raised when an eCAL measurement cannot be opened."""


@dataclass(frozen=True)
class EcalMessageSample:
    """Raw eCAL sample metadata preserving both send and receive timestamps."""

    channel: str
    snd_timestamp_ns: int
    rcv_timestamp_ns: int
    sequence: int


def _import_hdf5_module():
    try:
        return import_module("ecal.measurement.hdf5")
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via unit tests
        raise EcalDependencyError(
            "eclipse-ecal is required for measurement ingestion. Install the `eclipse-ecal` package."
        ) from exc


def _entry_sequence(entry: dict[str, int], fallback_index: int) -> int:
    if "counter" in entry:
        return int(entry["counter"])
    return fallback_index


def _require_timestamp(entry: dict[str, int], channel: str, field: str) -> int:
    if field not in entry:
        raise EcalMeasurementError(
            f"Entry for channel '{channel}' does not include timestamp field '{field}'."
        )
    return int(entry[field])


def load_measurement_entries(
    measurement_path: str,
    channels: Iterable[str] | None = None,
) -> list[EcalMessageSample]:
    """Load eCAL entries preserving both send and receive timestamps."""
    hdf5 = _import_hdf5_module()
    reader = hdf5.Meas(measurement_path, 0)

    if not reader.is_ok():
        raise EcalMeasurementError(f"Failed to open eCAL measurement at '{measurement_path}'.")

    try:
        available_channels = set(reader.get_channel_names())
        selected_channels = sorted(channels) if channels is not None else sorted(available_channels)

        entries_out: list[EcalMessageSample] = []
        for channel in selected_channels:
            if channel not in available_channels:
                continue

            entries = reader.get_entries_info(channel)
            for index, entry in enumerate(entries, start=1):
                entries_out.append(
                    EcalMessageSample(
                        channel=channel,
                        snd_timestamp_ns=_require_timestamp(entry, channel=channel, field="snd_timestamp"),
                        rcv_timestamp_ns=_require_timestamp(entry, channel=channel, field="rcv_timestamp"),
                        sequence=_entry_sequence(entry, fallback_index=index),
                    )
                )

        return entries_out
    finally:
        reader.close()


def load_measurement_samples(
    measurement_path: str,
    channels: Iterable[str] | None = None,
    timestamp_field: str = "rcv_timestamp",
) -> list[MessageSample]:
    """Load normalized samples from an eCAL recording using the selected timestamp basis."""
    if timestamp_field not in {"rcv_timestamp", "snd_timestamp"}:
        raise ValueError("timestamp_field must be either 'rcv_timestamp' or 'snd_timestamp'.")

    entries = load_measurement_entries(measurement_path=measurement_path, channels=channels)

    samples: list[MessageSample] = []
    for entry in entries:
        timestamp_ns = entry.rcv_timestamp_ns if timestamp_field == "rcv_timestamp" else entry.snd_timestamp_ns
        samples.append(
            MessageSample(
                channel=entry.channel,
                timestamp_ns=timestamp_ns,
                sequence=entry.sequence,
            )
        )
    return samples


def compute_latency_ns(samples: Iterable[EcalMessageSample]) -> list[int]:
    """Compute one-way latency estimate (receive - send) in nanoseconds."""
    return [sample.rcv_timestamp_ns - sample.snd_timestamp_ns for sample in samples]


def analyze_measurement(
    measurement_path: str,
    channels: Iterable[str] | None = None,
    timestamp_field: str = "rcv_timestamp",
) -> list[ChannelDropSummary]:
    """Load and analyze channel drops directly from an eCAL measurement recording."""
    samples = load_measurement_samples(
        measurement_path=measurement_path,
        channels=channels,
        timestamp_field=timestamp_field,
    )

    by_channel: dict[str, list[MessageSample]] = defaultdict(list)
    for sample in samples:
        by_channel[sample.channel].append(sample)

    return [analyze_channel(channel_samples) for channel_samples in by_channel.values()]
