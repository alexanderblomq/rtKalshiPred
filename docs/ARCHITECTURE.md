# Technical architecture

## Entry points and configuration

main.py is the main runtime CLI. It resolves a title/market, selects sources, loads
filesystem state, optionally syncs the RT reference and backfills, then runs a
finite or continuous polling loop. core.realtime_tomatometer also exposes the
engine's CLI. Package tools run with python -m; neither settings nor tests inject
subdirectories into the import path.

settings.py reads environment defaults. Source selection joins publication IDs
from data/critics/publication_registry.json to data/critics/source_rules.json.
scrapers.factory creates ArticleScraper, RSSScraper or SitemapScraper instances.
The engine defaults to enabled publications; the CLI minimal preset narrows this
to Variety, New Yorker and RogerEbert IDs. These names describe configuration,
not a live accessibility guarantee.

## Discovery to accepted review

1. ReviewDiscoverer searches recent source surfaces for a requested title;
   TitleSearchBackfiller also queries publication search pages during startup.
2. ReviewDropMonitor polls configured adapters for candidate URLs. It filters
   acknowledged URLs before applying its per-publication event budget and
   deduplicates emitted URLs across outlets. Discovery is refreshed each poll.
3. The engine dispatches candidates to scrape_review. ArticleScraper extracts
   headline, body, raw score, actual byline, date and absolute canonical URL.
4. Review-likeness and title matching qualify each record. Explicit conflicting
   years are rejected; short titles require a token match rather than a substring
   inside another word. This remains a similarity policy, not full film identity.
5. review_classifier returns a fresh probability. Parsed scores take an explicit
   shortcut; unscored records use the saved model or lexicon fallback. Grade
   intensity and probability of RT freshness still require semantic separation.
6. Worker failures become per-review retryable rejections. Probabilities must be
   finite and in [0,1]. Decisions are applied in deterministic URL order.
7. Accepted/permanently rejected decisions are written before source aliases are
   acknowledged. Failed processing can be retried if the URL remains discoverable.
   There is no durable retry scheduler independent of the source feed yet.

Accepted records retain outlet/critic/URL metadata, raw score, observed-at and
published-at times, probability, title confidence and review likeness. Full text,
model hashes and parser-version provenance are not yet retained in this record.

## Aggregation and state

The rolling calculated_tomatometer is 100 times the mean accepted fresh
probability. binary_tomatometer instead counts probabilities at least 0.5.
Official RT count/score are separate reference observations and are not merged
into this review population.

FileSystemRealtimeStateStore writes decision events, accepted/rejected rows and
snapshots as JSONL, and atomically replaces state.json. Hydration reconciles full
decision payloads with materialized review rows and restores URL aliases. An
interrupted final record without a newline is preserved in a sibling .incomplete
file before recovery; malformed complete records still fail visibly. Writes are
protected within one store instance, not across processes. Use a single writer
per title directory.

This is the working runtime backend. TradeLedger is a separate actual SQLite
database; it is not a SQLite implementation of the runtime state interface.

## Market path

market_resolver parses supported natural-language contract forms. kalshi_client
fetches/normalizes event markets and books. aggregate_predictor produces printed
recommendations; trading_signal independently plans event-level orders. They
currently use different score units and uncertainty assumptions and should be
consolidated before evaluating contract forecasts.

TradeLedger stores signals, quotes, intents, orders, fills and paper status.
PaperTradingEngine is a simplified local fill simulation; KalshiExecutor is
unverified live-execution library plumbing. The main CLI invokes a single optional
paper cycle, and its exchange snapshot is initially fetched at startup. It is not
a recurring, reconciled trading service. Fill-price units, paper/live isolation,
settlement, fees and PnL calculations remain repair work.

| Value | Intended units | Important boundary |
| --- | --- | --- |
| normalized_score | 0–1 grade fraction | A grade is not itself an observed RT verdict. |
| fresh_probability | 0–1 | Engine checks finite values and bounds. |
| calculated_tomatometer | 0–100 | Consensus over observed accepted reviews, not final-score calibration. |
| aggregate_predictor score/threshold | 0–1 | Separate from the event planner's percentage points. |
| trading_signal score/threshold | 0–100 | Some fraction conversion remains heuristic. |
| exchange price | Field-dependent | Existing cents/dollars heuristics and fill ingestion need unifying. |

## Preparation and evaluation

Registry building, publication enrichment and source-rule generation are in
pipelines/. Regeneration is not yet idempotent on checked-in artifacts and can
discard enrichment or alter classifications. Markdown parser profiles have stored
compiled counterparts, but their compiler is absent.

build_review_dataset collects RT labels/quotes and optionally article text.
models.trainer fits TF-IDF, publication/critic features and normalized grades with
logistic regression, then saves a model, calibration sidecar and metrics.
The committed historical bundle lacks the sidecar and uses a different
scikit-learn version. models.evaluate_review_classifier does not yet reproduce
all runtime shortcuts/calibration. A shared inference/evaluation contract and
film/time holdout are prerequisites for meaningful performance claims.

validate_rt_signal compares stored/refreshed state with reference scores and
supplied contract examples. It is descriptive research tooling, not a causal
market backtest. Lead-time measurement requires first-observed publication and
RT-incorporation histories that are not currently established.

## Verification

The offline demo supplies synthetic HTML through an injected scraper and uses
the real parser, filtering, classification, aggregation, filesystem state,
restart hydration and order-intent persistence. It does not exercise live HTTP
discovery or exchange fills. A separate integration test exercises the real
monitor and adapter against changing fake HTTP responses, including failure,
retry and restart. Subprocess tests verify retained package entrypoints without
test-only import setup.
