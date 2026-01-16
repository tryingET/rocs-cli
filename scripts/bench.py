from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from gen_bench_repo import gen_repo


def _run(cmd: list[str], *, env: dict[str, str]) -> float:
    t0 = time.perf_counter()
    subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    xs = sorted(samples)
    if pct <= 0:
        return xs[0]
    if pct >= 100:
        return xs[-1]
    k = (len(xs) - 1) * (pct / 100.0)
    i = int(k)
    frac = k - i
    if i + 1 < len(xs):
        return xs[i] * (1.0 - frac) + xs[i + 1] * frac
    return xs[i]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cmd", choices=["build", "validate", "lint"], default="build")
    p.add_argument("--n-concepts", type=int, default=500)
    p.add_argument("--runs", type=int, default=7, help="number of timed runs (warm)")
    p.add_argument("--out", default="artifacts/perf/bench.json")
    args = p.parse_args(argv)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        repo = gen_repo(td_path / "repo", n_concepts=int(args.n_concepts))

        cache_dir = td_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env["ROCS_CACHE_DIR"] = str(cache_dir)

        base_cmd = [sys.executable, "-m", "rocs_cli", str(args.cmd), "--repo", str(repo)]
        # keep machine output consistent; minimize console rendering
        if args.cmd in ("build", "validate", "lint"):
            base_cmd.append("--json")

        cold_ms = _run(base_cmd, env=env)
        warm: list[float] = []
        for _ in range(int(args.runs)):
            warm.append(_run(base_cmd, env=env))

        payload = {
            "schema_version": 1,
            "cmd": args.cmd,
            "n_concepts": int(args.n_concepts),
            "cold_ms": cold_ms,
            "warm_ms": warm,
            "warm_median_ms": _percentile(warm, 50),
            "warm_p95_ms": _percentile(warm, 95),
        }

        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
        print(json.dumps(payload, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
