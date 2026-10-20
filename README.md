# rtKalshiPred

Pre-RT Rotten Tomatoes signal engine for Kalshi movie markets.

Default recommended runtime path: Linux VM. Windows local runs are still useful for development and targeted debugging, but the repo is now documented and packaged around VM-first continuous scanning.

This repo is no longer a scaffold. It now has:
- a live critic/publication registry for Rotten Tomatoes outlets
- multi-outlet review discovery and scraping
- rolling predicted Rotten Tomatoes score state
- live Kalshi market fetch from market text or Kalshi URL
- contract-aware signal generation for `above`, `below`, `between`, and `fresh/rotten` markets
- a persistent trade ledger
- a Streamlit dashboard with predicted score, simulated P/L, and scraper-health coverage
- validation tooling for score error, review coverage, contract Brier score, and paper-trade P/L

## Current Status

Implemented now:
- RT critic/publication registry refresh and enrichment
- config-first scraper framework with `article`, `rss`, and `sitemap` adapters
- parser-profile workflow for AI/manual site-specific scraper tuning
- whole-registry scraper audit and health reporting
- review discovery, title matching, review filtering, and fresh/rotten classification
- rolling per-title state with restart-safe persistence
- live Kalshi market/event fetch and quote normalization
- threshold/range trade recommendation logic
- signal/quote/order/fill ledger schema
- dashboard and VM deployment path
- scheduled VM maintenance jobs for registry refresh, parser-profile compilation, scraper audit, and validation batches
- validation pipeline for real title batches

Still not fully complete:
- automatic Kalshi order submission
- live fill reconciliation from the exchange
- realized P/L from real orders
- full RT inclusion/ingestion-lag modeling
- production-grade multi-node worker orchestration

## Data Snapshot

Checked-in registry data currently includes:
- `1062` Rotten Tomatoes publications
- `1879` Rotten Tomatoes critics

Post-profile scraper audit currently shows:
- `988` supported scraper rules
- `869` connected sites
- `819` healthy non-noisy sites
- `119` failing sites
- `50` noisy sites

Those numbers come from:
- [scraper_coverage_report_post_profiles.json](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/scraper_coverage_report_post_profiles.json)

## Core Capabilities

### 1. Critic scraping
- builds RT registries and outlet rules
- discovers review URLs across the outlet registry
- scrapes headline, body, score, publish date, and critic name
- supports custom selector profiles compiled into `source_rules.json`

### 2. Rolling RT prediction
- startup backfill for already-published reviews
- live polling for new reviews
- title filtering and fresh/rotten classification
- rolling `calculated_tomatometer`
- persistent state with resume-after-restart behavior

### 3. Kalshi market integration
- accepts raw market text or a full Kalshi URL
- fetches live event/market snapshots
- normalizes YES/NO pricing
- supports RT market structures:
  - `be Fresh` / `be Rotten`
  - `score above X%`
  - `score below X%`
  - `score between X% and Y%`

### 4. Signal and ledger
- computes model probability vs market probability
- records signal snapshots and quote snapshots
- stores order intents, orders, and fills for future execution integration
- powers a simulated autotrading P/L curve

### 5. Validation and ops
- network doctor for runtime connectivity
- live-title validator for runtime health
- signal validator for score error, coverage, threshold accuracy, and paper-trade P/L
- Linux VM deployment path for always-on monitoring
- scheduled maintenance jobs and timer artifacts for continuous registry/rule/audit/validation upkeep

## Repo Structure

Runtime and orchestration:
- `main.py` - top-level CLI for title/market monitoring and live Kalshi integration
- `realtime_tomatometer.py` - startup backfill + live polling engine
- `dashboard.py` - Streamlit UI for Kalshi link input, predicted RT, P/L, and scraper health
- `state_store.py` - filesystem/SQLite runtime state stores
- `trade_ledger.py` - SQLite trade/signal/quote/order/fill ledger

Market and model:
- `market_resolver.py` - parses Kalshi-style RT contract text
- `kalshi_client.py` - live Kalshi market/event/orderbook fetch and URL parsing
- `aggregate_predictor.py` - market-level probability estimator from live snapshot evidence
- `trading_signal.py` - threshold/range contract signal logic
- `models/review_classifier.py` - fresh/rotten review classifier

Discovery and scraping:
- `review_drop_monitor.py`
- `discover_reviews.py`
- `title_search_backfill.py`
- `review_scraper.py`
- `scrapers/`

Registry/rules/profile tooling:
- `pipelines/build_critic_registry.py`
- `pipelines/enrich_publications.py`
- `pipelines/build_source_rules.py`
- `pipelines/audit_scraper_coverage.py`
- `pipelines/generate_parser_profile_stub.py`
- `pipelines/generate_problematic_parser_profiles.py`
- `pipelines/compile_parser_profiles.py`

Validation/deployment:
- `pipelines/doctor_network.py`
- `pipelines/validate_live_titles.py`
- `pipelines/validate_rt_signal.py`
- `deploy/vm/`
- `VM_DEPLOYMENT.md`

## Quick Start

For development on Windows:

```powershell
cd C:\Users\ablom\Downloads\RomaModel\rtKalshiPred
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Optional `.env` values:
- `RT_POLL_INTERVAL_SECONDS`
- `DEFAULT_EDGE_THRESHOLD`
- `LOG_LEVEL`
- `KALSHI_API_BASE_URL`

For always-on runtime, use the Linux VM path in [VM_DEPLOYMENT.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/VM_DEPLOYMENT.md).

## Typical Workflows

### Refresh registries and rules

```powershell
python pipelines/build_critic_registry.py
python pipelines/enrich_publications.py --only-missing-base-url --value-order --limit 100
python pipelines/build_source_rules.py
```

### Generate and compile parser profiles

Single outlet:
```powershell
python -m pipelines.generate_parser_profile_stub 411mania
python -m pipelines.compile_parser_profiles
```

Problematic outlets from the scraper audit:
```powershell
python -m pipelines.generate_problematic_parser_profiles --report scraper_coverage_report.json --output-dir data/critic_parser_profiles
python -m pipelines.compile_parser_profiles
```

### Audit the scraper registry

```powershell
python -m pipelines.audit_scraper_coverage --include-disabled --max-workers 24 --output scraper_coverage_report.json
```

### Discover reviews for a movie

```powershell
python discover_reviews.py "Animal Farm" --max-publications 100 --min-confidence 0.6
```

### Run the live engine from a raw movie title

```powershell
python main.py "Animal Farm" --input-is-title --publication-preset minimal --clean --health-report --iterations 0
```

### Run the live engine from a Kalshi URL

```powershell
python main.py "https://kalshi.com/markets/RT_ABOVE_80" --live-kalshi --clean
```

### Validate signal quality for a batch of titles

```powershell
python -m pipelines.validate_rt_signal --manifest data/validation/example_titles.json --publication-preset core --output data/validation/report.json
```

Fresh live rerun before validation:
```powershell
python -m pipelines.validate_rt_signal --manifest data/validation/example_titles.json --publication-preset core --refresh --backfill-max-publications 50 --output data/validation/report.json
```

### Launch the dashboard

```powershell
streamlit run dashboard.py
```

Dashboard now shows:
- Kalshi link input
- predicted Rotten Tomatoes score
- simulated autotrading P/L
- critic-site health summary from the latest scraper audit

## VM Operations

The default recommended deployment shape is:
- one Linux VM
- one long-running `rtkalshipred.service` per monitored title
- scheduled maintenance timers for registry/rule/audit/validation upkeep

Artifacts:
- `deploy/vm/run_monitor.sh`
- `deploy/vm/run_maintenance_job.sh`
- `deploy/vm/install_maintenance_timers.sh`
- `deploy/vm/rtkalshipred.service`
- `deploy/vm/rtkalshipred-*.service`
- `deploy/vm/rtkalshipred-*.timer`
- `deploy/vm/maintenance/*.env.example`

Maintenance jobs now supported out of the box:
- `registry-refresh`
- `parser-profile-compile`
- `scraper-audit`
- `title-validation`

See [VM_DEPLOYMENT.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/VM_DEPLOYMENT.md) for install and scheduling commands.

## Scraper Architecture

The scraper layer is config-first.

Main files:
- `publication_registry.json`
- `critic_registry.json`
- `source_rules.json`
- `data/critic_parser_profiles/`

Important behavior:
- `ArticleScraper` uses configured selectors first, heuristic fallbacks second
- parser profiles are markdown files with a JSON block that can be authored by AI or manually
- `compile_parser_profiles.py` merges them into `source_rules.json`
- `audit_scraper_coverage.py` tells you which outlets are failing or noisy

This is the intended scale path for the tricky long-tail outlets: generate a profile stub, inspect/fix selectors, compile, and rerun the audit.

## Runtime State and Ledger

Per-title runtime state:
- `accepted_reviews.jsonl`
- `rejected_events.jsonl`
- `events.jsonl`
- `snapshots.jsonl`
- `state.json`

Trade ledger tables:
- `signal_snapshots`
- `market_quote_snapshots`
- `order_intents`
- `orders`
- `fills`

The runtime state tracks what the engine has seen. The trade ledger tracks what the strategy believed, what the market was pricing, and eventually what actually got traded.

## Validation Path

To trust the signal, do not rely on architecture alone. Use:
- `pipelines/validate_rt_signal.py`

It measures:
- model score vs official RT score
- review coverage ratio vs official RT review count
- first/last review seen times
- contract-level Brier score
- simulated paper-trade P/L

Use a manifest with 20-50 recent films to determine whether the strategy has real edge.

## VM Path

Use a Linux VM as the default runtime, not just as a fallback.

Start with:
```bash
python pipelines/doctor_network.py
python pipelines/validate_live_titles.py "Animal Farm" --publication-preset minimal --skip-rt-sync --backfill-max-publications 3
```

Then follow:
- [VM_DEPLOYMENT.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/VM_DEPLOYMENT.md)

## Testing

Recommended Windows test ergonomics:
- always use a repo-local `--basetemp`
- disable pytest cache provider when temp cleanup is flaky
- prefer focused test invocations while iterating on scraper/deployment changes

Targeted:
```powershell
python -m pytest tests\test_validate_rt_signal.py -q --basetemp=data/pytest-basetemp-validate-signal-repo -p no:cacheprovider
```

Full suite:
```powershell
python -m pytest tests -q --basetemp=data/pytest-basetemp-full -p no:cacheprovider
```

If cleanup still fails on Windows:
- close any Streamlit/Python processes still holding files
- rerun with a fresh repo-local `--basetemp` path
- keep VM smoke/ops validation separate from local pytest runs

## Related Docs

- [USAGE_GUIDE.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/USAGE_GUIDE.md)
- [RUNBOOK.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/RUNBOOK.md)
- [PIPELINE.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/PIPELINE.md)
- [VM_DEPLOYMENT.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/VM_DEPLOYMENT.md)
- [TODO.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/TODO.md)
- [RT_critics_recon.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/RT_critics_recon.md)
- [review_classifier-TODO.md](/C:/Users/ablom/Downloads/RomaModel/rtKalshiPred/review_classifier-TODO.md)
