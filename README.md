# ravine-api examples

Two starter scripts:

| File | Purpose |
|---|---|
| [`simple_bot.py`](simple_bot.py) | Paper-trade memecoins using `/v1/snapshot` decisions |
| [`trajectories_explorer.py`](trajectories_explorer.py) | Inspect labeled lifecycle data from `/v1/trajectories` |

Both require an API key — email `dbrouill@gmail.com` to get one.

---

## trajectories_explorer.py — quick recipe

```bash
export RAVINE_API_KEY=your_key
python trajectories_explorer.py                # top recent homeruns
python trajectories_explorer.py --label loss   # losers (most are losers!)
python trajectories_explorer.py --label win --json | jq '.rows[0]'
```

Each row carries the T+0/T+5/T+15/T+30/T+1h/T+24h capture of a labeled token. Train your own model, validate a thesis, or build a "what did winners look like at T+5?" dashboard.

---

# simple_bot.py

A 100-line paper-trading bot that consumes [ravine-api](https://kno-innovation.com/api/) to make exit-or-hold decisions on Solana memecoins.

**Pure paper. No wallet. No real orders.** Pedagogical demo.

## What it does

Every 3 minutes:
1. Calls `GET /v1/snapshot` for live token list
2. Opens a paper position on healthy tokens (ravine HOLD, p_rupture < 0.30, fresh entry)
3. Closes positions when ravine flags `QUANTUM_EXIT_NOW` or p_rupture ≥ 0.70
4. Logs everything to `simple_bot.jsonl`

## Run

```bash
pip install requests   # or use stdlib urllib (no deps)
python simple_bot.py
```

Watch the log:

```bash
tail -f simple_bot.jsonl | jq -c 'select(.event=="PAPER_SELL")'
```

## Tweak

- `PAPER_STAKE_USD = 5.0` — paper position size
- `POLL_S = 180` — match the ravine-api 3-min refresh
- `len(positions) < 3` — max concurrent positions
- Entry filter: `decision == "HOLD" and p < 0.30 and n_obs >= 6 and 0.0 <= roi_so_far <= 0.15`

## What this is NOT

- Not financial advice
- Not a full trading bot (no wallet, no slippage, no real PnL)
- Not optimized — it's a starting point

## Build your own

Fork this and add:
- Real wallet integration (Jupiter swap aggregator + Solana SDK)
- Better entry logic (combine multiple signals)
- Custom thresholds calibrated to your risk profile
- Persistence + restart-resume

The ravine-api is one tool in the chain. Compose it with your own data and execution layer.

## When you outgrow free tier

If you start running this 24/7 and see meaningful PnL movement, you'll quickly hit the free tier ceilings:

| Free | Pro |
|---|---|
| 10K calls/day | unlimited |
| 3-min snapshot | **30-second snapshot** |
| top 50 tokens | top 200+ |
| alpha wallet counts | **full wallet IDs (copy-tradeable)** |
| poll-only | **webhooks on EXIT_NOW** |

Most serious bots upgrade once they're consistent. **Pro is $49/mo or 2 SOL/mo**:
[https://kno-innovation.com/api/#pro](https://kno-innovation.com/api/#pro)

MIT.
