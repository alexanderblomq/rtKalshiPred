"""Exercise real module boundaries without conftest's former import workaround."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = [
    "main", "core.realtime_tomatometer", "scrapers.discover_reviews",
    "scrapers.title_search_backfill", "models.trainer",
    "models.evaluate_review_classifier", "pipelines.build_critic_registry",
    "pipelines.build_source_rules", "pipelines.build_review_dataset",
    "pipelines.enrich_publications", "pipelines.benchmark_enrichment_workers",
    "pipelines.validate_rt_signal",
]


def run_module(module, *args):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, "-m", module, *args], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=20,
    )


@pytest.mark.parametrize("module", ENTRYPOINTS)
def test_module_help_without_import_bootstrap(module):
    result = run_module(module, "--help")
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_offline_startup_and_unsupported_state_backend(tmp_path):
    flags = ["Offline Probe", "--input-is-title", "--skip-backfill",
             "--skip-rt-sync", "--iterations", "0", "--state-root", str(tmp_path)]
    result = run_module("main", *flags)
    assert result.returncode == 0, result.stderr
    assert "Loaded existing state" in result.stdout
    unsupported = run_module("main", *flags, "--state-backend", "sqlite")
    assert unsupported.returncode == 2
    assert "invalid choice" in unsupported.stderr
