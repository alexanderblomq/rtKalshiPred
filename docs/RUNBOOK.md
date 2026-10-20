# Runbook

Primary operating model: Linux VM. Use Windows mainly for local development, targeted debugging, and documentation updates.

## Daily Start

From the repo root:

```powershell
cd C:\Users\ablom\Downloads\RomaModel\rtKalshiPred
```

Windows-local ad hoc refresh:

```powershell
python pipelines/build_critic_registry.py
python pipelines/enrich_publications.py --only-missing-base-url --value-order --limit 100
python pipelines/build_source_rules.py
```

VM-first production path:
- keep title monitors running under systemd
- keep maintenance timers enabled
- use the dashboard and generated reports for health checks instead of manual repeated local runs

Check timer state:

```bash
sudo systemctl list-timers 'rtkalshipred-*'
sudo systemctl status rtkalshipred
```

## Start Monitoring A Film

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report --iterations 100 --sleep-seconds 60
```

For a quicker startup test:

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report --iterations 0
```

On a VM, the preferred path is editing `/etc/rtkalshipred/rtkalshipred.env` and restarting:

```bash
sudo systemctl restart rtkalshipred
journalctl -u rtkalshipred -f
```

## Scheduled Maintenance Jobs

VM maintenance timers now cover:
- registry refresh
- parser-profile compilation
- scraper audit
- title validation batches

Install or reinstall:

```bash
sudo bash deploy/vm/install_maintenance_timers.sh
```

Manual one-shot runs:

```bash
bash deploy/vm/run_maintenance_job.sh registry-refresh
bash deploy/vm/run_maintenance_job.sh parser-profile-compile
bash deploy/vm/run_maintenance_job.sh scraper-audit
bash deploy/vm/run_maintenance_job.sh title-validation
```

Timer-owned env files:
- `/etc/rtkalshipred/maintenance/registry-refresh.env`
- `/etc/rtkalshipred/maintenance/parser-profile-compile.env`
- `/etc/rtkalshipred/maintenance/scraper-audit.env`
- `/etc/rtkalshipred/maintenance/title-validation.env`

## What You Should See

Immediate output:

- existing state loaded
- current resumed predicted RT score
- startup backfill message

Then cycle output:

- predicted RT
- accepted review count
- newly accepted review count
- latest accepted review
- health counters for backfill and polling

## Important Files During A Run

- `data/live/animal-farm/state.json`
- `data/live/animal-farm/accepted_reviews.jsonl`
- `data/live/animal-farm/rejected_events.jsonl`
- `data/live/animal-farm/events.jsonl`
- `data/live/animal-farm/snapshots.jsonl`

VM ops/report files:
- `/opt/rtKalshiPred/data/ops/logs/`
- `/opt/rtKalshiPred/data/ops/reports/scraper_coverage_report_latest.json`
- `/opt/rtKalshiPred/data/ops/reports/rt_signal_validation_latest.json`

## If The Score Looks Wrong

1. Inspect `accepted_reviews.jsonl`
2. Inspect `rejected_events.jsonl`
3. Run one-shot discovery:

```powershell
python discover_reviews.py "Animal Farm" --max-publications 100 --min-confidence 0.6
```

4. Inspect a suspicious review manually with `review_scraper.py`
5. Run the network doctor:

```powershell
python pipelines/doctor_network.py
```
6. Run the title validator on a narrow subset:

```powershell
python pipelines/validate_live_titles.py "Animal Farm" --publication-preset minimal --skip-rt-sync --backfill-max-publications 3
```
7. On the VM, inspect the latest scheduled audit and validation reports before changing code.

## If Startup Looks Stalled

The engine should now print initial status immediately. Full-registry backfill can still take time after that.

Try a narrower run:

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report --iterations 0 --backfill-max-publications 25
```

Or tune workers:

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report --iterations 0 --backfill-publication-workers 24 --backfill-scrape-workers 24
```

On a VM, also confirm maintenance timers are not overlapping unusually:

```bash
sudo systemctl status rtkalshipred-scraper-audit.timer
sudo systemctl status rtkalshipred-title-validation.timer
```

## If You Need A Fresh Run

Delete only the specific title state folder:

- `data/live/animal-farm/`

Then rerun the engine.

CLI alternative:

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report --reset-state --iterations 0
```

## Retrain The Classifier

```powershell
python trainer.py --dataset data/processed/review_training_dataset_approved_rt_only.jsonl
python evaluate_review_classifier.py
```

## Windows Test Ergonomics

Preferred local test pattern:

```powershell
python -m pytest tests\test_dashboard.py -q --basetemp=data/pytest-basetemp-dashboard-worker6 -p no:cacheprovider
```

For larger runs:

```powershell
python -m pytest tests -q --basetemp=data/pytest-basetemp-full-worker6 -p no:cacheprovider
```

If pytest still reports cleanup permission issues:
- use a new `--basetemp` directory name
- stop lingering Python/Streamlit processes
- avoid mixing live local runs and pytest on the same state/log paths

## Current Do-Not-Do List

- Do not assume the internal score equals official RT.
- Do not assume every accepted review will be RT-counted.
- Do not use the current repo for unattended automatic betting.
- Do not treat Windows-local Python networking problems as an application bug before running `pipelines/doctor_network.py`.
