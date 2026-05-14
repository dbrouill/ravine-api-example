"""simple_bot.py — Minimal example: paper-trade pump.fun memecoins using ravine-api.

Polls /v1/snapshot every 3 minutes, opens "paper" positions on tokens with
HOLD + healthy ROI, closes on QUANTUM_EXIT_NOW. Logs every decision.

NOT a production trader. NO real wallet, NO real orders. Pedagogical demo.

⚠ FREE TIER LIMITS ⚠
This example uses the free tier:
  - Snapshot refreshed every 3 minutes (vs 30s with Pro)
  - Top 50 tokens only (vs 200+ with Pro)
  - Alpha wallet COUNTS only (no IDs to copy-trade)
  - No webhooks — you must poll
By the time you see EXIT_NOW here, the move may be 3 min old. Real bots use Pro:
  https://kno-innovation.com/api/#pro

Usage:
    python simple_bot.py
"""
from __future__ import annotations
import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

API_BASE = "https://api.kno-innovation.com"
POLL_S = 180
PAPER_STAKE_USD = 5.0
LOG = Path("simple_bot.jsonl")

positions: dict[str, dict] = {}     # mint -> {entry_mcap, entry_ts, stake}
realized_pnl_usd = 0.0


def http_get(path: str) -> dict:
    req = urllib.request.Request(f"{API_BASE}{path}",
                                 headers={"User-Agent": "ravine-example-bot/0.1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def log(event: dict) -> None:
    event["ts"] = time.time()
    with LOG.open("a") as f:
        f.write(json.dumps(event) + "\n")
    print(json.dumps(event))


def open_paper(token: dict) -> None:
    mint = token["mint"]
    positions[mint] = {
        "entry_mcap": token["mcap_usd"],
        "entry_ts": time.time(),
        "stake_usd": PAPER_STAKE_USD,
        "p_rupture_at_entry": token.get("p_rupture"),
    }
    log({"event": "PAPER_BUY", "mint": mint,
         "entry_mcap": token["mcap_usd"], "stake_usd": PAPER_STAKE_USD,
         "p_rupture": token.get("p_rupture")})


def close_paper(mint: str, cur_mcap: float, reason: str) -> None:
    global realized_pnl_usd
    p = positions.pop(mint, None)
    if not p:
        return
    roi = cur_mcap / p["entry_mcap"] - 1
    pnl_usd = p["stake_usd"] * roi
    realized_pnl_usd += pnl_usd
    log({"event": "PAPER_SELL", "mint": mint, "reason": reason,
         "entry_mcap": p["entry_mcap"], "exit_mcap": cur_mcap,
         "roi_pct": round(roi * 100, 2),
         "pnl_usd": round(pnl_usd, 4),
         "cumulative_pnl_usd": round(realized_pnl_usd, 4)})


def cycle() -> None:
    try:
        snap = http_get("/v1/snapshot")
    except Exception as e:
        log({"event": "FETCH_ERR", "error": str(e)})
        return

    seen = set()
    for tok in snap.get("entries", []):
        mint = tok["mint"]
        seen.add(mint)
        cur_mcap = tok["mcap_usd"]
        decision = tok.get("quantum_decision")
        p = tok.get("p_rupture") or 0

        if mint in positions:
            # Existing position: exit on EXIT_NOW or hard rupture proba
            if decision == "QUANTUM_EXIT_NOW" or p >= 0.70:
                close_paper(mint, cur_mcap, f"quantum_exit p={p:.2f}")
        else:
            # No position yet: open if healthy + low rupture risk + cheap entry
            n_obs = tok.get("n_obs", 0)
            roi_so_far = tok.get("roi_since_first_observed") or 0
            if (decision == "HOLD" and p < 0.30 and n_obs >= 6
                    and 0.0 <= roi_so_far <= 0.15
                    and len(positions) < 3):
                open_paper(tok)

    # Tokens dropped from snapshot (no longer watched) — close at last known mcap
    for mint in list(positions):
        if mint not in seen:
            entry = positions[mint]["entry_mcap"]
            close_paper(mint, entry * 0.5, "dropped_from_snapshot")  # assume -50% loss

    log({"event": "CYCLE_END", "n_positions": len(positions),
         "realized_pnl_usd": round(realized_pnl_usd, 4)})

    # Pedagogical nudge: surface what the free tier hides.
    if realized_pnl_usd < 0 and len(positions) == 0:
        print("─── note: 3-min refresh means EXIT signals lag. "
              "Pro = 30s refresh + webhooks. https://kno-innovation.com/api/#pro ───")


def main():
    print(f"simple_bot starting → {API_BASE}, log → {LOG}")
    while True:
        cycle()
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
