from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

from pipelines.enrich_publications import enrich_publications, sort_publications_by_value


def load_publications(publication_registry_path: str) -> List[Dict[str, object]]:
    return json.loads(Path(publication_registry_path).read_text(encoding="utf-8"))


def select_sample(publications: List[Dict[str, object]], sample_size: int) -> List[Dict[str, object]]:
    unresolved = [publication for publication in publications if publication.get("rt_source_path")]
    ordered = sort_publications_by_value(unresolved)
    return ordered[:sample_size]


def run_benchmark(publication_registry_path: str, sample_size: int, worker_counts: List[int]) -> None:
    publications = load_publications(publication_registry_path)
    sample = select_sample(publications, sample_size)

    print(f"Sample size: {len(sample)}")
    print(f"Publication ids: {[publication['publication_id'] for publication in sample[:10]]}")

    for workers in worker_counts:
        started = time.perf_counter()
        enriched, enriched_count = enrich_publications(sample, max_workers=workers)
        elapsed = time.perf_counter() - started
        rate = len(enriched) / elapsed if elapsed else 0.0
        print(
            json.dumps(
                {
                    "workers": workers,
                    "elapsed_seconds": round(elapsed, 2),
                    "publications": len(enriched),
                    "with_site_base_url": enriched_count,
                    "pubs_per_second": round(rate, 2),
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark enrichment throughput across worker counts.")
    parser.add_argument("--publication-registry", default="data/critics/publication_registry.json")
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--workers", nargs="+", type=int, default=[4, 8, 12, 16, 20, 24])
    args = parser.parse_args()

    run_benchmark(args.publication_registry, args.sample_size, args.workers)
