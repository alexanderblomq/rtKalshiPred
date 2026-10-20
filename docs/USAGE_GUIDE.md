# Usage Guide

## Scope

`rtKalshiPred` is currently usable as a critic-ingestion and rolling pre-RT score engine.

Default recommendation:
- use a Linux VM for continuous scanning and scheduled upkeep
- use Windows local runs for development, spot checks, and parser tuning

What works now:

- Rotten Tomatoes critic and publication registry refresh
- publication enrichment and source-rule generation
- cross-publication review discovery
- direct review scraping from critic outlets
- baseline fresh/rotten classification
- startup backfill for already-published critic-site reviews
- live polling for newly surfaced review URLs
- persistent per-title state with resume-after-restart behavior

What is still incomplete:

- Kalshi orchestration and execution
- RT inclusion / ingestion-lag modeling
- full production-grade aggregate forecasting
- uniformly reliable scraping across every publication

## Setup

From the repo root:

```powershell
cd C:\Users\ablom\Downloads\RomaModel\rtKalshiPred
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

For always-on operation, stop here and switch to the VM flow in [VM_DEPLOYMENT.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/VM_DEPLOYMENT.md).

Optional `.env` values:

- `RT_POLL_INTERVAL_SECONDS`
- `DEFAULT_EDGE_THRESHOLD`
- `LOG_LEVEL`
- `KALSHI_API_BASE_URL`

## Refreshing Registry Data

Refresh Rotten Tomatoes critics and publications:

```powershell
python pipelines/build_critic_registry.py
```

Enrich publications:

```powershell
python pipelines/enrich_publications.py --only-missing-base-url --value-order --limit 100
```

Regenerate source rules:

```powershell
python pipelines/build_source_rules.py
```

On the VM, these tasks should normally run from the maintenance scheduler instead of manual shells.

Maintenance job entrypoints:

```bash
bash deploy/vm/run_maintenance_job.sh registry-refresh
bash deploy/vm/run_maintenance_job.sh parser-profile-compile
bash deploy/vm/run_maintenance_job.sh scraper-audit
bash deploy/vm/run_maintenance_job.sh title-validation
```

## Training And Evaluation

Train the baseline review classifier:

```powershell
python trainer.py --dataset data/processed/review_training_dataset_approved_rt_only.jsonl
```

Evaluate the trained model:

```powershell
python evaluate_review_classifier.py
```

Model artifacts are written under:

- `model_output/review_classifier/model.joblib`
- `model_output/review_classifier/metrics.json`
- `model_output/review_classifier/evaluation_report.json`

## One-Shot Discovery

Search the registry for likely reviews of a title:

```powershell
python discover_reviews.py "Animal Farm" --max-publications 100 --min-confidence 0.6
```

Use this when you want to inspect candidate review pages before starting the live engine.

## Live Monitoring

Primary runtime:

```powershell
python realtime_tomatometer.py "Animal Farm" --clean --iterations 20 --sleep-seconds 60
```

Recommended testing commands:

```powershell
python realtime_tomatometer.py "Animal Farm" --clean --iterations 0
python realtime_tomatometer.py "Animal Farm" --clean --iterations 10 --sleep-seconds 30
python realtime_tomatometer.py "Animal Farm" --clean --iterations 0 --backfill-publication-workers 24 --backfill-scrape-workers 24
```

For production use, prefer `main.py` on the VM with `--state-backend sqlite` and systemd.

Clean mode prints:

- current predicted RT score
- number of accepted reviews
- number of new reviews accepted in the current cycle
- latest accepted review summary

## Runtime Flow

For a title like `Animal Farm`, the engine does:

1. Load persisted state from `data/live/<title-slug>/`
2. Print current resumed score immediately
3. Run startup backfill across the configured publication registry
4. Scrape and classify accepted matching reviews
5. Persist accepted reviews, rejected events, snapshots, and engine events
6. Continue polling for newly surfaced review URLs
7. Update the internal calculated Tomatometer on each accepted review

## Stored Data

Per-title state lives under:

- `data/live/<title-slug>/`

Files:

- `accepted_reviews.jsonl`
- `rejected_events.jsonl`
- `events.jsonl`
- `snapshots.jsonl`
- `state.json`

Meaning:

- `accepted_reviews.jsonl`: accepted review observations used in the rolling score
- `rejected_events.jsonl`: candidates that were rejected, with rejection reasons
- `events.jsonl`: audit-style engine events like poll start/completion and review decisions
- `snapshots.jsonl`: append-only score snapshots over time
- `state.json`: latest materialized state for fast resume

## Resetting A Title

If you want a title to start from zero again, clear its state directory:

- `data/live/animal-farm/`

Do this only for that title, not the entire `data/live/` tree.

CLI alternative:

```powershell
python realtime_tomatometer.py "Animal Farm" --clean --reset-state --iterations 0
```

If you want to isolate a run completely, use a separate state root:

```powershell
python realtime_tomatometer.py "Animal Farm" --clean --state-root data/live_experiments --iterations 0
```

## Recommended Operating Practice

- Prefer `--clean` mode for routine use.
- Let backfill complete before judging the score.
- Check `accepted_reviews.jsonl` for obvious false positives.
- When validating a new title, first run one-shot discovery manually.
- Retrain after materially improving scraped text coverage or source rules.
- Start with monitoring and analysis, not autonomous trading.
- Let the VM maintenance timers keep registries, parser profiles, and audits fresh.

## Known Caveats

- Some outlets may return `403` or block scraping.
- Some discovery surfaces contain newsletters, roundups, or guides.
- Title ambiguity can still produce false matches.
- Full-registry startup backfill can take noticeable time.
- Persisted state resumes automatically unless you clear the title folder.
- The live score is an internal pre-RT estimate, not the official Rotten Tomatoes score.

## Current Reliability Boundary

The system is suitable now for:

- research
- live monitoring
- pre-RT review timeline building
- rolling sentiment estimation from critic sites

It is not yet suitable for:

- autonomous real-money trading
- assuming all accepted reviews will be counted by RT
- production-grade fully automatic market execution

## Windows Test Ergonomics

On Windows, prefer repo-local pytest temp roots:

```powershell
python -m pytest tests\test_validate_rt_signal.py -q --basetemp=data/pytest-basetemp-usage-guide -p no:cacheprovider
```

Full suite:

```powershell
python -m pytest tests -q --basetemp=data/pytest-basetemp-usage-guide-full -p no:cacheprovider
```

This avoids the temp-dir cleanup failures that can occur with default pytest temp handling on this machine.
