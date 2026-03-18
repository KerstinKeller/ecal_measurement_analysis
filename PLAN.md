# Development Plan (TDD-first)

## Goal
Build Python tooling to analyze eCAL recording timestamp behavior and message drops, with explicit support for identifying synchronized multi-channel losses.

## Phase 1 (completed)
- [x] Define core data model (`MessageSample`, `DropEvent`, `ChannelDropSummary`).
- [x] Implement sequence-gap based drop detection per channel.
- [x] Implement cross-channel overlap aggregation for synchronized loss windows.
- [x] Add unit tests first and implement until green.

## Phase 2 (next)
- [ ] Build eCAL adapter layer using Python bindings to read measurements directly.
- [ ] Persist normalized data as Parquet/CSV for reproducible post-processing.
- [ ] Add fixture-based integration tests against small sample recordings.

## Phase 3 (next)
- [ ] Add visualization module (timeline + channel/time heatmap).
- [ ] Add CLI command(s): `extract`, `analyze`, `plot`, `report`.
- [ ] Export static report bundle (JSON summary + PNG/SVG charts).

## Phase 4 (next)
- [ ] Add pattern analysis: periodic losses, burst detection, and channel clustering.
- [ ] Add CI checks (`pytest`, formatting, linting).
