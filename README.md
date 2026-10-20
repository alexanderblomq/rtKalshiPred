# rtKalshiPred

A Python research tool for collecting film reviews from publication websites, estimating their fresh/rotten consensus, and exploring Rotten Tomatoes contracts on Kalshi.

The hypothesis is that some reviews appear on publication sites before they are reflected in RT. This repository contains ingestion and modeling tools for studying that hypothesis. A persistent timing advantage or profitable trading strategy has not been established.

## Run the offline example

The example uses synthetic HTML and quotes, exercises the real parser, review filter, title matcher, classifier, engine, persistence and order planner, and makes no external requests.

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python demo.py
~~~

Expected result: four accepted reviews, a 75% internal consensus, two hypothetical order intents, and four recovered reviews with no new duplicates after restart. Output uses a temporary directory by default. To keep the JSONL state and SQLite ledger:

~~~bash
.venv/bin/python demo.py --state-root data/live/offline-example
~~~

Direct dependency versions are pinned to the environment used for verification: Python 3.14.7. The example supplies explicit Fresh/Rotten verdicts and does not load the older saved ML model. A fresh environment installation has not been independently verified on every platform.

## Monitor a title

From the repository root, replace the example title with the exact film and release year:

~~~bash
.venv/bin/python main.py "Your Film (2026)" --input-is-title \
  --publication-preset minimal --skip-rt-sync \
  --backfill-max-publications 3 --iterations 1 \
  --state-root data/live_reviews --clean --health-report
~~~

For ongoing polling, use --continuous instead of --iterations:

~~~bash
.venv/bin/python main.py "Your Film (2026)" --input-is-title \
  --publication-preset minimal --skip-rt-sync \
  --backfill-max-publications 3 --continuous --sleep-seconds 60 \
  --state-root data/live_reviews --clean --health-report
~~~

--iterations 0 runs startup only. It does not mean continuous operation. Ctrl-C stops monitoring. The engine uses filesystem state; the SQLite database is the separate trade ledger. Only enabled sources are constructed by the engine, and the minimal preset further selects three outlets. Current website accessibility and extraction quality must be checked against actual output; catalog size is not a coverage guarantee.

Official RT baseline parsing is experimental. To request it, omit --skip-rt-sync and supply a manually verified --rt-title-path m/your_film_slug. Avoid relying on fuzzy RT search as an authoritative film identifier.

## Architecture

~~~mermaid
flowchart LR
    Config[Publication registry and source rules] --> Discovery[Feed and title-search discovery]
    Discovery --> Parser[Article extraction]
    Parser --> Filter[Review filter and title match]
    Filter --> Classifier[Freshness probability]
    Classifier --> State[Rolling consensus and durable state]
    State --> Planner[Experimental contract probabilities]
    Quotes[Kalshi quotes] --> Planner
    Planner --> Ledger[Order intents and paper ledger]
~~~

| Location | Responsibility |
| --- | --- |
| main.py | CLI configuration, startup backfill, finite/continuous polling, experimental market output. |
| core/realtime_tomatometer.py | Review processing, probability aggregation, acceptance/rejection and restart hydration. |
| core/state_store.py | JSONL logs, atomic materialized state, replay and interrupted-tail recovery. |
| scrapers/ | Article/RSS/sitemap adapters, title matching, score normalization, discovery and RT reference parsing. |
| models/ | Text/metadata classifier, training and evaluation. |
| market/ | Market parsing, exchange adapter, probability models, paper execution and SQLite ledger. |
| pipelines/ | Registry, enrichment, source-rule, dataset and validation tools. |
| data/critics/ | Checked-in publication/critic catalog and scraper rules. |
| data/critic_parser_profiles/ | Research profiles represented in stored rules; no profile compiler currently ships. |
| data/demo/reviews.json | Synthetic input for the offline integration example. |
| tests/ | Component, subprocess entrypoint and repeated-ingestion regression checks. |

Accepted reviews contribute their fresh probabilities to an arithmetic mean. That current observed subset is not a calibrated forecast of the final settlement-time RT score. Explicit grade conversion, learned sentiment, and RT's actual fresh verdict are distinct concepts.

Discovery pages are fetched again on each poll. URLs are acknowledged after durable acceptance or permanent rejection; transient processing failures can be retried. State is designed for one writer per title. An incomplete final JSONL append is saved separately and recovered; malformed complete records still raise an error.

## Development and tools

~~~bash
.venv/bin/python -m pytest tests -q
.venv/bin/python -m models.trainer --help
.venv/bin/python -m models.evaluate_review_classifier --help
.venv/bin/python -m pipelines.build_review_dataset --help
.venv/bin/python -m pipelines.validate_rt_signal --help
~~~

Run package tools with python -m from the repository root. Commands no longer depend on source-directory injection into sys.path. Use separate output directories for experiments; some preparation/refresh commands overwrite existing artifacts.

## Current limits and next work

- The catalog has 1,062 publications, but many rules are unverified placeholders or unsupported source types. Validate a small outlet set before expanding.
- Historical parser profiles do not prove current access or extraction. Rule regeneration needs an idempotence check and profile compilation needs restoring.
- The large training dataset contains RT snippets, not full article bodies. Evaluate on unseen films with features available at the actual observation time.
- The saved model was built with scikit-learn 1.8.0, while the pinned environment uses 1.9.1. Calibration/provenance are incomplete; retrain and validate a complete bundle before relying on ML outputs.
- Contract recommendations and event planning still use different probability implementations. Unify units, uncertainty and settlement boundaries.
- Quote refresh, exchange authentication, fill units, paper/live separation and portfolio accounting need further repair. Existing PnL helpers are not evidence of realized trading returns.
- The CLI's paper option performs one cycle. There is no supported autonomous real-money trading workflow, dashboard, or packaged VM service.

See [usage](docs/USAGE_GUIDE.md), [operations](docs/RUNBOOK.md), [architecture](docs/ARCHITECTURE.md), and [deployment status](docs/VM_DEPLOYMENT.md).
