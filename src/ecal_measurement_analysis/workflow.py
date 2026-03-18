from __future__ import annotations

WORKFLOW_STEPS = [
    "Extract metadata from eCAL recordings with sequence numbers and timestamps per channel.",
    "Normalize data into a single table: channel, timestamp_ns, sequence.",
    "Run channel-level drop analysis to compute expected messages and drop intervals.",
    "Aggregate overlapping drop windows to detect multi-channel synchronized loss.",
    "Visualize timelines and heatmaps to inspect periodicity and shared failures.",
    "Export a report with top loss intervals, per-channel loss ratios, and candidate root causes.",
]

TOOLING_RECOMMENDATIONS = {
    "core": [
        "Python 3.10+",
        "pytest for TDD",
        "pandas for tabular preprocessing",
        "matplotlib/plotly for timeline and heatmap visualizations",
    ],
    "adapters": [
        "eCAL Python bindings to iterate measurement files",
        "CSV/Parquet export for reproducible offline analysis",
    ],
    "quality": [
        "Synthetic fixture recordings for regression tests",
        "CI pipeline running pytest and lint checks",
    ],
}
