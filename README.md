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
