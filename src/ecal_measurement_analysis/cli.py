from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .analysis import ChannelDropSummary, DropEvent
from .ecal_adapter import analyze_measurement, load_measurement_entries
from .persistence import (
    write_ecal_entries_csv,
    write_ecal_entries_parquet,
)
from .reporting import write_summary_report_json
from .visualization import plot_channel_drop_heatmap, plot_drop_timeline


def _parse_channels(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    channels = [item.strip() for item in raw.split(",") if item.strip()]
    return channels or None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecal-measurement-analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract")
    extract.add_argument("measurement_path")
    extract.add_argument("--output", required=True)
    extract.add_argument("--format", choices=["csv", "parquet"], default="csv")
    extract.add_argument("--channels")

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("measurement_path")
    analyze.add_argument("--output", required=True)
    analyze.add_argument("--channels")
    analyze.add_argument("--timestamp-field", choices=["rcv_timestamp", "snd_timestamp"], default="rcv_timestamp")

    plot = subparsers.add_parser("plot")
    plot.add_argument("summary_json")
    plot.add_argument("--output-dir", required=True)

    report = subparsers.add_parser("report")
    report.add_argument("measurement_path")
    report.add_argument("--output-dir", required=True)
    report.add_argument("--channels")
    report.add_argument("--timestamp-field", choices=["rcv_timestamp", "snd_timestamp"], default="rcv_timestamp")

    return parser


def _load_summaries_from_report(summary_path: str | Path) -> list[ChannelDropSummary]:
    payload = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    return [
        ChannelDropSummary(
            channel=item["channel"],
            total_samples=item["total_samples"],
            expected_samples=item["expected_samples"],
            lost_samples=item["lost_samples"],
            loss_ratio=item["loss_ratio"],
            drop_events=[DropEvent(**event) for event in item["drop_events"]],
        )
        for item in payload["channels"]
    ]


def _run_extract(args: argparse.Namespace) -> int:
    entries = load_measurement_entries(args.measurement_path, channels=_parse_channels(args.channels))
    if args.format == "csv":
        write_ecal_entries_csv(entries, args.output)
    else:
        write_ecal_entries_parquet(entries, args.output)
    return 0


def _run_analyze(args: argparse.Namespace) -> int:
    summaries = analyze_measurement(
        args.measurement_path,
        channels=_parse_channels(args.channels),
        timestamp_field=args.timestamp_field,
    )
    write_summary_report_json(summaries, args.output)
    return 0


def _run_plot(args: argparse.Namespace) -> int:
    summaries = _load_summaries_from_report(args.summary_json)
    output_dir = Path(args.output_dir)
    plot_drop_timeline(summaries, output_dir / "timeline.png")
    plot_channel_drop_heatmap(summaries, output_dir / "heatmap.png")
    return 0


def _run_report(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    summaries = analyze_measurement(
        args.measurement_path,
        channels=_parse_channels(args.channels),
        timestamp_field=args.timestamp_field,
    )
    summary_path = output_dir / "summary.json"
    write_summary_report_json(summaries, summary_path)
    plot_drop_timeline(summaries, output_dir / "timeline.png")
    plot_channel_drop_heatmap(summaries, output_dir / "heatmap.png")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        return _run_extract(args)
    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "plot":
        return _run_plot(args)
    if args.command == "report":
        return _run_report(args)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
