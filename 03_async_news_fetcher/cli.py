"""
Async News Fetcher — CLI
=========================
Usage:
    python cli.py                          # fetch all sources
    python cli.py --sources "BBC News" "Reuters"
    python cli.py --sources "TechCrunch" "Hacker News" --limit 5
    python cli.py --list-sources           # show available sources
    python cli.py --benchmark              # show timing comparison
"""

import argparse
import sys
import time

from fetcher import SOURCES, run_fetch


# ── Display ───────────────────────────────────────────────────────

def print_results(results, benchmark):
    print(f"\n{'='*60}")
    print(f"  News Fetcher — {benchmark['fetched_at']}")
    print(f"  {benchmark['successful']}/{benchmark['total_sources']} sources OK  |  "
          f"{benchmark['total_articles']} articles  |  "
          f"{benchmark['total_duration']}s total")
    print(f"{'='*60}\n")

    for result in results:
        if result.success:
            print(f"  [{result.source}]  ({len(result.articles)} articles, {result.duration:.2f}s)")
            for i, article in enumerate(result.articles, 1):
                print(f"    {i:>2}. {article.title[:80]}")
                if article.link:
                    print(f"        {article.link[:70]}")
            print()
        else:
            print(f"  [{result.source}]  ERROR: {result.error}\n")

    if benchmark["failed"] > 0:
        print(f"  {benchmark['failed']} source(s) failed (network/timeout).")


def print_benchmark(results, total_duration):
    print(f"\n{'─'*50}")
    print(f"  Benchmark — Async fetch")
    print(f"{'─'*50}")
    print(f"  {'Source':<20} {'Articles':>8}  {'Time':>8}  Status")
    print(f"  {'─'*20} {'─'*8}  {'─'*8}  {'─'*6}")
    for r in sorted(results, key=lambda x: x.duration):
        status = "OK" if r.success else "FAIL"
        count  = len(r.articles) if r.success else 0
        print(f"  {r.source:<20} {count:>8}  {r.duration:>6.2f}s  {status}")
    print(f"{'─'*50}")
    print(f"  Total (concurrent): {total_duration:.2f}s")
    sequential_est = sum(r.duration for r in results)
    print(f"  Est. sequential:    {sequential_est:.2f}s")
    print(f"  Speedup:            {sequential_est/total_duration:.1f}x faster\n")


# ── CLI ───────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Fetch news headlines from multiple RSS sources concurrently.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python cli.py
  python cli.py --sources "BBC News" "TechCrunch"
  python cli.py --limit 5 --benchmark
  python cli.py --list-sources
        """,
    )
    parser.add_argument(
        "--sources", nargs="+", metavar="SOURCE",
        help="Source names to fetch (default: all). Use --list-sources to see names.",
    )
    parser.add_argument(
        "--limit", type=int, default=10, metavar="N",
        help="Max articles per source (default: 10)",
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Show per-source timing table and speedup vs sequential",
    )
    parser.add_argument(
        "--list-sources", action="store_true",
        help="List all available sources and exit",
    )
    return parser


def main():
    args = build_parser().parse_args()

    if args.list_sources:
        print("\nAvailable sources:")
        for name, url in SOURCES.items():
            print(f"  {name:<20}  {url}")
        print()
        return

    # Resolve sources
    if args.sources:
        invalid = [s for s in args.sources if s not in SOURCES]
        if invalid:
            print(f"Unknown sources: {invalid}")
            print(f"Run with --list-sources to see valid names.")
            sys.exit(1)
        selected = {k: v for k, v in SOURCES.items() if k in args.sources}
    else:
        selected = SOURCES

    print(f"\nFetching {len(selected)} source(s) concurrently...", flush=True)

    results, total_duration, benchmark = run_fetch(selected)

    print_results(results, benchmark)

    if args.benchmark:
        print_benchmark(results, total_duration)


if __name__ == "__main__":
    main()
