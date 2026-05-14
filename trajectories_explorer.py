"""trajectories_explorer.py — Discover what pump.fun homeruns looked like at T+5.

Polls /v1/trajectories?label=homerun, then prints — for each labeled token —
the T+5 features that came BEFORE the homerun outcome was knowable. Use this
as a starting point for your own model or pattern research.

⚠ FREE TIER LIMITS ⚠
  - Last 24h only
  - 50 newest labeled mints
  - Public features only (bonding, replies, mcap, ROI, label)
  - Alpha features (deployer reputation, top holders, alpha-wallet count)
    require Pro: https://kno-innovation.com/api/#pro

Usage:
    export RAVINE_API_KEY=your_key
    python trajectories_explorer.py
    python trajectories_explorer.py --label win
    python trajectories_explorer.py --label loss --json   # raw output
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

API_BASE = "https://api.kno-innovation.com"
API_KEY  = os.environ.get("RAVINE_API_KEY", "")


def fetch(label: str | None = None) -> dict:
    if not API_KEY:
        print("Set RAVINE_API_KEY env var. Get one: dbrouill@gmail.com")
        sys.exit(1)
    qs = f"?label={urllib.parse.quote(label)}" if label else ""
    req = urllib.request.Request(
        f"{API_BASE}/v1/trajectories{qs}",
        headers={"X-API-Key": API_KEY, "User-Agent": "trajectories-explorer/0.1"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def print_table(payload: dict) -> None:
    rows = payload.get("rows", [])
    if not rows:
        print(f"No trajectories returned. cache_age={payload.get('cache_age_s')}s")
        return

    print(f"{'mint':<14} {'symbol':<10} {'bp_t5':>6} {'rv_t5':>6} {'bp_t30':>7} {'mcap_1h':>9} {'roi_1h':>7} {'roi_24h':>8} {'label'}")
    print("-" * 90)
    for r in rows:
        dna  = r.get("dna")  or {}
        t30  = r.get("t30")  or {}
        t1h  = r.get("t1h")  or {}
        t24h = r.get("t24h") or {}
        print(f"{(r.get('mint') or '')[:13]:<14} "
              f"{(dna.get('symbol') or '')[:9]:<10} "
              f"{dna.get('bonding_pct_t5') or 0:>6.3f} "
              f"{dna.get('reply_velocity') or 0:>6.1f} "
              f"{t30.get('bonding_pct') or 0:>7.3f} "
              f"${(t1h.get('mcap') or 0):>8,.0f} "
              f"{(t1h.get('roi_pct') or 0):>+7.1f}% "
              f"{(t24h.get('roi_pct') or 0):>+7.1f}% "
              f"{t24h.get('label3') or '-'}")

    # Funnel hint
    pro = payload.get("pro_features_available")
    if pro:
        print()
        print(f"💡 Pro tier unlocks: {', '.join(pro.get('alpha_features_pro', []))}")
        print(f"   → {pro.get('upgrade_url')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--label", choices=["homerun", "win", "loss"], default="homerun",
                    help="filter by outcome label (default: homerun)")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of table")
    args = ap.parse_args()

    payload = fetch(args.label)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Fetched {payload.get('total_matched')} {args.label} trajectories "
              f"(window={payload.get('window_s', 0) // 3600}h, "
              f"cache_age={payload.get('cache_age_s')}s)\n")
        print_table(payload)


if __name__ == "__main__":
    main()
