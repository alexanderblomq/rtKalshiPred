# Usage guide

Start with the [README](../README.md) offline example. All commands below run from the repository root using the existing virtual environment.

## Local development

~~~bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python demo.py
~~~

The demo uses synthetic review pages and market quotes. Its HTML parser, classifier, state engine, restart recovery and order-intent writes are real; its source and quote inputs are fixtures.

## Discovery and monitoring

~~~bash
.venv/bin/python -m scrapers.discover_reviews "Your Film (2026)" --help
.venv/bin/python -m scrapers.title_search_backfill --help
.venv/bin/python main.py "Your Film (2026)" --input-is-title \
  --publication-preset minimal --skip-rt-sync --backfill-max-publications 3 \
  --iterations 1 --state-root data/live_reviews --clean --health-report
~~~

Use the actual film title/year. Inspect accepted reviews before trusting the internal consensus. --continuous polls until interrupted; --iterations 0 performs startup only. Explicit release years help reject remakes with conflicting years, but similarity matching still needs real-world validation.

For an official baseline, use a verified --rt-title-path and omit --skip-rt-sync. RT parsing is experimental. A successful HTTP request is not proof of correct movie or score identity.

## State

The filesystem store writes one title directory under --state-root:

- accepted_reviews.jsonl and rejected_events.jsonl record decisions.
- events.jsonl records recovery-capable engine events.
- snapshots.jsonl records internal score history.
- state.json is the latest materialized state.

Keep one writer per title directory. Interrupted trailing records are preserved in a sibling .incomplete file. Complete malformed records stop loading so corruption remains visible. Use a fresh --state-root for isolated experiments. --reset-state deletes a title's existing state and should be used only deliberately.

## Preparation and evaluation

Use module entrypoints:

~~~bash
.venv/bin/python -m pipelines.build_critic_registry --help
.venv/bin/python -m pipelines.enrich_publications --help
.venv/bin/python -m pipelines.build_source_rules --help
.venv/bin/python -m pipelines.build_review_dataset --help
.venv/bin/python -m models.trainer --help
.venv/bin/python -m models.evaluate_review_classifier --help
.venv/bin/python -m pipelines.validate_rt_signal --help
~~~

Help is safe; executing preparation commands may refresh/overwrite checked-in artifacts. Source-rule regeneration currently changes classifications and needs idempotence repair before use as unattended maintenance. The profile compiler advertised by older documents is absent.

The saved classifier and its stored metrics are historical. Current training creates calibration output not present in the committed bundle. Evaluation and live inference still need unifying, with a holdout by film/time. Batch validation currently produces descriptive snapshot metrics and illustrative contract payoffs, not a chronological market backtest.

## Market features

main.py --live-kalshi fetches an initial market snapshot for experimental recommendations. --paper-trade-cycle performs one local simulated cycle, not a recurring strategy. Do not interpret the existing accounting helpers as verified portfolio PnL. Authentication and current exchange payload compatibility remain unfinished; there is no supported funded-trading command.
