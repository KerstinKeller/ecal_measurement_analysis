from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .analysis import MessageSample
from .ecal_adapter import EcalMessageSample


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_message_samples_csv(samples: Iterable[MessageSample], output_path: str | Path) -> None:
    path = Path(output_path)
    _ensure_parent(path)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["channel", "timestamp_ns", "sequence"])
        writer.writeheader()
        for sample in samples:
            writer.writerow(asdict(sample))


def read_message_samples_csv(input_path: str | Path) -> list[MessageSample]:
    path = Path(input_path)
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            MessageSample(
                channel=row["channel"],
                timestamp_ns=int(row["timestamp_ns"]),
                sequence=int(row["sequence"]),
            )
            for row in reader
        ]


def write_ecal_entries_csv(entries: Iterable[EcalMessageSample], output_path: str | Path) -> None:
    path = Path(output_path)
    _ensure_parent(path)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["channel", "snd_timestamp_ns", "rcv_timestamp_ns", "sequence"],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow(asdict(entry))


def read_ecal_entries_csv(input_path: str | Path) -> list[EcalMessageSample]:
    path = Path(input_path)
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            EcalMessageSample(
                channel=row["channel"],
                snd_timestamp_ns=int(row["snd_timestamp_ns"]),
                rcv_timestamp_ns=int(row["rcv_timestamp_ns"]),
                sequence=int(row["sequence"]),
            )
            for row in reader
        ]


def _pyarrow_modules():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "Parquet support requires pyarrow. Install `pyarrow` to use parquet persistence."
        ) from exc
    return pa, pq


def write_ecal_entries_parquet(entries: Iterable[EcalMessageSample], output_path: str | Path) -> None:
    pa, pq = _pyarrow_modules()
    path = Path(output_path)
    _ensure_parent(path)

    rows = [asdict(entry) for entry in entries]
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def read_ecal_entries_parquet(input_path: str | Path) -> list[EcalMessageSample]:
    _, pq = _pyarrow_modules()
    table = pq.read_table(Path(input_path))
    return [EcalMessageSample(**row) for row in table.to_pylist()]


def write_message_samples_parquet(samples: Iterable[MessageSample], output_path: str | Path) -> None:
    pa, pq = _pyarrow_modules()
    path = Path(output_path)
    _ensure_parent(path)

    rows = [asdict(sample) for sample in samples]
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)


def read_message_samples_parquet(input_path: str | Path) -> list[MessageSample]:
    _, pq = _pyarrow_modules()
    table = pq.read_table(Path(input_path))
    return [MessageSample(**row) for row in table.to_pylist()]
