# Deployment status and prerequisites

This checkout does not include a packaged VM deployment. The older systemd scripts, timers, dashboard and network-doctor/title-validator commands were removed; instructions referring to those files are obsolete.

First prove the supported local path in the [README](../README.md): offline demo, regression suite, a small title monitor, repeated source refresh and restart recovery. The verified environment used Python 3.14.7 with the direct dependency versions recorded in requirements.txt.

A future Linux service should run main.py with --continuous, an absolute state root, an exact title/year and a small verified source set. Its working directory must be the repository root because registry/model defaults are relative. Use one process per title state directory.

Before deployment, provide and verify:

- Service installation, stop/restart handling and log retention.
- Fresh-source and quote-age health reporting.
- Reproducible source configuration and a compatible model/calibration bundle.
- State retention/backup and single-writer ownership.
- Failure/retry behavior across actual network failures.

Review monitoring and paper research are separate from funded trading. Exchange authentication, price normalization, order reconciliation, risk limits and portfolio accounting require additional work before a live-execution deployment.
