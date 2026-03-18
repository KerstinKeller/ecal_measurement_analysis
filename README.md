# eCAL Measurement Analysis

A Python toolkit for analyzing eCAL recording timestamp integrity, drop behavior, synchronized multi-channel loss windows, and higher-level drop patterns.

---

## What this project does

Given eCAL measurement metadata (channel, timestamps, sequence counters), the toolkit can:

- detect per-channel sequence gaps and estimate missing message windows,
- compute channel-level loss ratios,
- find synchronized cross-channel drop windows,
- detect **periodic** drop behavior,
- detect **bursty** drop behavior,
- cluster channels by overlap similarity of drop windows,
- export static report bundles for offline review.

---

## Installation Guide

### 1) Prerequisites

- Python 3.10+
- `pip`
- Optional but recommended: a virtual environment (`venv`)

### 2) Standard install

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

This installs runtime dependencies, including:

- `eclipse-ecal` (measurement ingestion)
- `pyarrow` (Parquet persistence)
- `matplotlib` (plot generation)

### 3) Development install

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

Development extras include:

- `pytest`
- `ruff`

### 4) Verify installation

```bash
ecal-measurement-analysis --help
pytest
```

---

## CLI Usage Guide

The package installs a console command:

```bash
ecal-measurement-analysis <subcommand> [options]
```

### Subcommand: `extract`

Extract raw entry metadata from an eCAL measurement into CSV or Parquet.

```bash
ecal-measurement-analysis extract /path/to/measurement \
  --output artifacts/entries.csv \
  --format csv \
  --channels cam,lidar
```

Options:

- `measurement_path` (required)
- `--output` (required)
- `--format {csv,parquet}` (default: `csv`)
- `--channels` (comma-separated channel list)

### Subcommand: `analyze`

Run drop analysis on a measurement and export `summary.json`.

```bash
ecal-measurement-analysis analyze /path/to/measurement \
  --output artifacts/summary.json \
  --timestamp-field rcv_timestamp
```

Options:

- `measurement_path` (required)
- `--output` (required)
- `--channels` (optional)
- `--timestamp-field {rcv_timestamp,snd_timestamp}` (default: `rcv_timestamp`)

### Subcommand: `plot`

Create static plots from an existing `summary.json`.

```bash
ecal-measurement-analysis plot artifacts/summary.json \
  --output-dir artifacts/report
```

Outputs:

- `timeline.png`
- `heatmap.png`

### Subcommand: `report`

One-shot command: analyze + report export.

```bash
ecal-measurement-analysis report /path/to/measurement \
  --output-dir artifacts/report \
  --timestamp-field rcv_timestamp
```

Outputs:

- `summary.json`
- `timeline.png`
- `heatmap.png`

---

## Python API Usage Guide

### Core adapter + analysis

```python
from ecal_measurement_analysis import analyze_measurement

summaries = analyze_measurement("/path/to/measurement")
for summary in summaries:
    print(summary.channel, summary.loss_ratio, summary.lost_samples)
```

### Report generation

```python
from ecal_measurement_analysis import analyze_measurement, write_summary_report_json

summaries = analyze_measurement("/path/to/measurement")
write_summary_report_json(summaries, "artifacts/summary.json")
```

### Pattern analysis (Phase 4)

```python
from ecal_measurement_analysis import (
    analyze_measurement,
    detect_periodic_losses,
    detect_drop_bursts,
    cluster_channels_by_overlap,
)

summaries = analyze_measurement("/path/to/measurement")

for summary in summaries:
    periodic = detect_periodic_losses(summary)
    bursts = detect_drop_bursts(summary, max_separation_ns=50_000_000)
    print(summary.channel, periodic, bursts)

clusters = cluster_channels_by_overlap(summaries)
print(clusters)
```

---

## Report Format (`summary.json`)

The report includes:

- `channels`: per-channel drop summaries and events,
- `synchronized_windows`: overlapping windows across 2+ channels,
- `patterns`:
  - `periodic_losses`,
  - `bursts`,
  - `channel_clusters`,
- `totals`: overall expected/lost counts and global loss ratio.

---

## Development / Quality

### Run tests

```bash
pytest
```

### Run lints

```bash
ruff check .
```

### CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml` and runs:

- `pytest`
- `ruff check .`

---

## Troubleshooting

- **`eclipse-ecal` import errors**: install or verify compatible eCAL Python bindings.
- **Parquet errors**: ensure `pyarrow` is available.
- **Plot errors**: ensure `matplotlib` is installed.
- **No drop events in plots**: heatmap/timeline may be sparse or empty if channels have no inferred losses.

---

## Roadmap status

- Phase 1: ✅ complete
- Phase 2: ✅ complete
- Phase 3: ✅ complete
- Phase 4: ✅ complete (pattern analysis + CI checks)
