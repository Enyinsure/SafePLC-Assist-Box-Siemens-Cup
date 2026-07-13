#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from benchmark.generation.build_benchmark_120 import CASES_PATH
from scripts.run_full_360 import PROJECT_ROOT, run_benchmark

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "runtime" / "benchmark120_v1"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run SafePLC Benchmark-120 against real FULL Chroma assets.")
    parser.add_argument("--cases", default=str(CASES_PATH))
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    return run_benchmark(
        cases_path=Path(args.cases).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        case_ids=args.case_id,
        categories=args.category,
        max_cases=max(0, args.max_cases),
        resume=args.resume,
        start_index=max(0, args.start_index),
        stop_on_error=args.stop_on_error,
    )


if __name__ == "__main__":
    raise SystemExit(main())
