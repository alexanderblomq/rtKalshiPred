# VM Deployment

This is the default recommended runtime path for `rtKalshiPred`. It avoids the Windows-local `python.exe` networking issues we saw and gives you a stable always-on runtime with scheduled upkeep.

## Target Shape

Recommended first deployment:

- Ubuntu 24.04 or Debian 12 VM
- 2 vCPU / 4 GB RAM minimum
- Python 3.11 or 3.12
- SQLite backend first
- `minimal` or `core` publication preset first
- systemd timers for registry/rule/audit/validation maintenance

Good providers:

- Hetzner
- DigitalOcean
- Vultr
- Linode / Akamai
- AWS Lightsail

## 1. Create the VM

Provision a Linux VM and SSH into it.

Install system packages:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip build-essential
```

## 2. Clone the Repo

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone <YOUR_REPO_URL> rtKalshiPred
sudo chown -R "$USER":"$USER" /opt/rtKalshiPred
cd /opt/rtKalshiPred
```

## 3. Create the Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Sanity Check Networking

Before you run the live engine, verify outbound access:

```bash
python pipelines/doctor_network.py
```

Expected outcome:

- all probes should return `"ok": true`

If they do not, stop here and fix VM networking first.

## 5. Validate a Small Subset

Run a narrow validation before starting a long-lived service:

```bash
python pipelines/validate_live_titles.py "Animal Farm" --publication-preset minimal --skip-rt-sync --backfill-max-publications 3
```

What you want to see:

- `scraper_failures` is low
- `title_search_candidate_urls` is not always zero
- fetches succeed for at least some outlets

## 6. Prepare Service Config

Create the service user:

```bash
sudo useradd --system --home /opt/rtKalshiPred --shell /usr/sbin/nologin rtkalshi || true
sudo chown -R rtkalshi:rtkalshi /opt/rtKalshiPred
```

Create the config directory:

```bash
sudo mkdir -p /etc/rtkalshipred
sudo cp deploy/vm/rtkalshipred.env.example /etc/rtkalshipred/rtkalshipred.env
sudo chown root:root /etc/rtkalshipred/rtkalshipred.env
sudo chmod 640 /etc/rtkalshipred/rtkalshipred.env
```

Edit:

```bash
sudo nano /etc/rtkalshipred/rtkalshipred.env
```

Suggested first config:

```dotenv
TITLE=Animal Farm
STATE_ROOT=/opt/rtKalshiPred/data/live_vm
STATE_BACKEND=sqlite
SQLITE_PATH=/opt/rtKalshiPred/data/live_vm/realtime_state.sqlite3
PUBLICATION_PRESET=minimal
SLEEP_SECONDS=60
ITERATIONS=0
BACKFILL_MAX_PUBLICATIONS=25
POLL_WORKERS=24
PROCESS_WORKERS=24
SKIP_RT_SYNC=0
RESET_STATE_ON_START=0
```

If the title is ambiguous, set:

```dotenv
RT_TITLE_PATH=m/animal_farm_2025
```

## 7. Install the systemd Service

```bash
sudo cp deploy/vm/rtkalshipred.service /etc/systemd/system/rtkalshipred.service
sudo systemctl daemon-reload
sudo systemctl enable rtkalshipred
sudo systemctl start rtkalshipred
```

Check status:

```bash
sudo systemctl status rtkalshipred
journalctl -u rtkalshipred -f
```

## 8. Install Maintenance Timers

The repo now includes scheduled maintenance artifacts for:
- registry refresh
- parser-profile generation/compilation
- scraper audit
- title validation batches

Install them:

```bash
sudo bash deploy/vm/install_maintenance_timers.sh
```

Review and edit the copied env files:

```bash
sudo nano /etc/rtkalshipred/maintenance/registry-refresh.env
sudo nano /etc/rtkalshipred/maintenance/parser-profile-compile.env
sudo nano /etc/rtkalshipred/maintenance/scraper-audit.env
sudo nano /etc/rtkalshipred/maintenance/title-validation.env
```

Check schedules:

```bash
sudo systemctl list-timers 'rtkalshipred-*'
```

Default timer cadence:
- `registry-refresh`: daily `03:15 UTC`
- `parser-profile-compile`: daily `03:45 UTC`
- `scraper-audit`: daily `04:15 UTC`
- `title-validation`: daily `05:00 UTC`

Manual runs:

```bash
bash deploy/vm/run_maintenance_job.sh registry-refresh
bash deploy/vm/run_maintenance_job.sh parser-profile-compile
bash deploy/vm/run_maintenance_job.sh scraper-audit
bash deploy/vm/run_maintenance_job.sh title-validation
```

## 9. Runtime Files

Default SQLite/live state:

- `/opt/rtKalshiPred/data/live_vm/realtime_state.sqlite3`
- `/opt/rtKalshiPred/data/live_vm/<title-slug>/runtime.log` if `main.py` is used with the default log path

Useful commands:

```bash
python pipelines/doctor_network.py
python pipelines/validate_live_titles.py "Animal Farm" --publication-preset minimal
python main.py "Animal Farm" --input-is-title --publication-preset minimal --state-backend sqlite --clean --health-report
```

Maintenance outputs:
- `/opt/rtKalshiPred/data/ops/logs/`
- `/opt/rtKalshiPred/data/ops/reports/scraper_coverage_report_latest.json`
- `/opt/rtKalshiPred/data/ops/reports/rt_signal_validation_latest.json`

## 10. Recommended Rollout Order

1. Prove networking with `doctor_network.py`
2. Validate one title with `minimal`
3. Run the service on one title
4. Install maintenance timers
5. Move to `core`
6. Add more titles as separate services or separate env files

## 11. Operating Model

For multiple titles, prefer one service per title/config file rather than one giant process.

That gives you:

- simpler restart semantics
- simpler state partitioning
- clearer logs
- easier debugging per movie
- independent validation manifests and trade-ledger state if you later automate execution

## 12. Windows Development Note

Use Windows for code changes and focused tests, but keep long-running monitoring and scheduled jobs on the VM.

Suggested Windows pytest pattern:

```powershell
python -m pytest tests -q --basetemp=data/pytest-basetemp-vm-docs -p no:cacheprovider
```

## 13. What This Does Not Solve

This VM path solves the local Windows networking blocker. It does not by itself solve:

- outlet anti-bot responses
- review coverage quality
- RT ingestion timing uncertainty
- final trading execution logic

But it gives you a stable place to run the scanner continuously, which is the right next step.
