from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .analysis import ChannelDropSummary


def _matplotlib_modules():
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Visualization requires matplotlib. Install `matplotlib` to use plotting.") from exc
    return plt


def plot_drop_timeline(
    channel_summaries: Iterable[ChannelDropSummary],
    output_path: str | Path,
    title: str = "Drop Timeline",
) -> Path:
    plt = _matplotlib_modules()
    summaries = list(channel_summaries)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, max(2, len(summaries) * 0.6)))
    for index, summary in enumerate(summaries):
        for event in summary.drop_events:
            width = max(event.end_ns - event.start_ns, 1)
            ax.broken_barh([(event.start_ns, width)], (index - 0.35, 0.7), facecolors="tab:red", alpha=0.7)

    ax.set_yticks(list(range(len(summaries))))
    ax.set_yticklabels([summary.channel for summary in summaries])
    ax.set_xlabel("Timestamp (ns)")
    ax.set_title(title)
    ax.grid(True, axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_channel_drop_heatmap(
    channel_summaries: Iterable[ChannelDropSummary],
    output_path: str | Path,
    bins: int = 50,
    title: str = "Channel Drop Heatmap",
) -> Path:
    plt = _matplotlib_modules()
    summaries = list(channel_summaries)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    all_bounds = [event.start_ns for summary in summaries for event in summary.drop_events] + [
        event.end_ns for summary in summaries for event in summary.drop_events
    ]

    fig, ax = plt.subplots(figsize=(10, max(2, len(summaries) * 0.6)))
    if not all_bounds:
        ax.text(0.5, 0.5, "No drop events", ha="center", va="center")
        ax.set_axis_off()
    else:
        min_ns = min(all_bounds)
        max_ns = max(all_bounds)
        span = max(max_ns - min_ns, 1)
        matrix = []

        for summary in summaries:
            row = [0] * bins
            for event in summary.drop_events:
                start_bin = int((event.start_ns - min_ns) * bins / span)
                end_bin = int((event.end_ns - min_ns) * bins / span)
                start_bin = max(0, min(start_bin, bins - 1))
                end_bin = max(0, min(end_bin, bins - 1))
                for idx in range(start_bin, end_bin + 1):
                    row[idx] = 1
            matrix.append(row)

        ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap="Reds")
        ax.set_yticks(list(range(len(summaries))))
        ax.set_yticklabels([summary.channel for summary in summaries])
        ax.set_xlabel("Time bin")
        ax.set_title(title)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
