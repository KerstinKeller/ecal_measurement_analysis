# eCAL Measurement Analysis

This repository bootstraps a **test-driven Python toolkit** for analyzing timestamp integrity and message drops in eCAL recordings.

## Proposed workflow

1. Metadata extraction from eCAL recordings:
   - Per sample: `channel`, `timestamp_ns`, `sequence`.
2. Normalization:
   - Store in one schema (DataFrame or table) for deterministic replay.
3. Channel-level analysis:
   - Detect sequence gaps and estimate exact missing windows.
   - Compute loss ratio per channel.
4. Cross-channel correlation:
   - Merge overlapping drop windows.
   - Flag synchronized loss events across multiple channels.
5. Visualization:
   - Timeline view of drop windows.
   - Heatmap (channel vs. time) for pattern discovery.
6. Reporting:
   - Persist JSON/CSV summary artifacts for each measurement batch.

## TDD strategy

- Start with synthetic sequence fixtures.
- Encode expected loss windows in unit tests.
- Add adapter tests once eCAL measurement readers are integrated.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```


## eCAL integration (Phase 2 progress)

The project now includes a direct adapter for `eclipse-ecal`:

- `load_measurement_entries(path, channels=None)`
  - Reads metadata from eCAL measurement files via `ecal.measurement.hdf5.Meas`.
  - Preserves both send and receive clocks in `EcalMessageSample(channel, snd_timestamp_ns, rcv_timestamp_ns, sequence)`.
- `load_measurement_samples(path, channels=None, timestamp_field="rcv_timestamp")`
  - Converts raw eCAL entries into `MessageSample(channel, timestamp_ns, sequence)` using either `rcv_timestamp` or `snd_timestamp`.
- `compute_latency_ns(entries)`
  - Calculates per-sample one-way latency estimate as `rcv_timestamp_ns - snd_timestamp_ns`.
- `analyze_measurement(path, ...)`
  - Loads samples and runs channel-wise drop analysis using existing core analyzers.

Install dependencies:

```bash
pip install -e .
```


## Persistence helpers

Normalized outputs can be persisted for reproducible post-processing:

- CSV: `write_message_samples_csv`, `read_message_samples_csv`, `write_ecal_entries_csv`, `read_ecal_entries_csv`
- Parquet: `write_message_samples_parquet`, `read_message_samples_parquet`, `write_ecal_entries_parquet`, `read_ecal_entries_parquet`

A fixture-backed integration path exists under `tests/fixtures/sample_measurement_entries.json` and `tests/test_persistence.py` to validate extract -> persist -> analyze behavior.
