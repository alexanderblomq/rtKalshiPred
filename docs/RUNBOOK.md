# Operations runbook

Current supported scope: local review monitoring, offline integration examples, and research tooling. No systemd service or dashboard ships in this checkout.

## Before a monitoring run

1. Run the offline example and regression suite.
2. Choose an exact title/year, a small source preset, and an isolated state root.
3. Leave RT reference fetching disabled unless its movie path has been verified.
4. Check startup/backfill/poll counters and manually inspect accepted URLs.

~~~bash
.venv/bin/python demo.py
.venv/bin/python -m pytest tests -q
.venv/bin/python main.py "Your Film (2026)" --input-is-title \
  --publication-preset minimal --skip-rt-sync --backfill-max-publications 3 \
  --continuous --sleep-seconds 60 --state-root data/live_reviews \
  --clean --health-report
~~~

--continuous runs until Ctrl-C; --iterations 0 runs startup only. State uses filesystem logs. The separate trading ledger uses SQLite.

## If ingestion is empty or looks wrong

Inspect the title directory's runtime.log, accepted_reviews.jsonl, rejected_events.jsonl and events.jsonl. Distinguish no candidate URLs, a source fetch failure, low title confidence, low review likeness, and classifier processing failure. Transient failures remain eligible for later polls; accepted/permanently rejected URLs are acknowledged.

A publication in the catalog is not necessarily enabled, supported, accessible or correctly parsed. Check the selected IDs and source rules. Verify title/year, canonical URL, body and actual byline for suspicious records.

If a final append is incomplete, startup preserves its bytes in a sibling .incomplete file and emits a warning. Retain that file for diagnosis. A malformed complete record stops loading; preserve a copy before investigating. One process should own a title's state directory.

For a new experiment, choose a new --state-root instead of deleting the previous run. Existing tracked live/debug snapshots are historical artifacts and should not be treated as validated observations.

## Known operating boundaries

Website layouts, paywalls and access policies can block extraction. There is no current whole-registry health guarantee or verified RT ingestion-lag measurement. Do not schedule registry/rule refresh blindly; regeneration and profile compilation require further repair.

The CLI paper feature executes one cycle and its accounting is not validated for trading performance. No live order workflow or deployment was verified as part of the local ingestion repair.
