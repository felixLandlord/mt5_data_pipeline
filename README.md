# MT5 Data Fetcher — README

A single Python script that connects to a running MetaTrader 5 terminal on Windows
and exports historical OHLC candlestick data or raw tick data to CSV files.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Windows 10/11** | The `MetaTrader5` Python package is Windows-only. Will not run on macOS or Linux. |
| **MetaTrader 5 terminal** | Must be installed, open, and logged into a broker account before running the script. |
| **Python 3.8 – 3.11** | 3.12+ is not officially tested by MetaQuotes. 64-bit Python required. |
| **Broker history loaded** | In MT5, open a chart for your symbol and scroll left to preload the full history. MT5 only exposes bars that have been downloaded to the terminal. |

---

## Package Installation

Run this in a regular Windows Command Prompt or PowerShell (**not** inside WSL):

```
pip install MetaTrader5 pandas
```

That's all you need. Both packages pull in their own dependencies automatically.

---

## Environment

- Run everything in **native Windows Python** — not WSL, not Docker, not a Linux VM.
- The `MetaTrader5` package communicates with the MT5 terminal via a local Windows pipe.
  It will silently fail or error in any non-Windows environment.
- A **64-bit Python** installation is required; 32-bit is unsupported.

---

## Setup Guide

1. Install MT5 from your broker and log in.
2. Open a chart for the symbol you want (e.g. EURUSD). Scroll all the way left to
   trigger history download. Wait until it stops loading.
   *(Tools → Options → Charts → "Max bars in history" — set this high, e.g. 500000.)*
3. Keep MT5 running in the background.
4. Install Python packages (see above).
5. Place `mt5_data_fetcher.py` anywhere on your Windows machine.
6. Edit the **CONFIG section** at the top of the file (see next section).
7. Run: `python mt5_data_fetcher.py`

---

## How to Use

All settings live in the `# CONFIGURATION` block at the top of the script.
You never need to edit anything below the `# END OF CONFIGURATION` line.

### Key settings

| Setting | What it does |
|---|---|
| `MODE` | `"ohlc"` (default) fetches candlestick bars. `"tick"` fetches raw tick data. |
| `SYMBOL` | Instrument name exactly as shown in MT5, e.g. `"EURUSD"`, `"XAUUSD"`, `"US30"`. |
| `DATE_FROM` / `DATE_TO` | Date range in UTC. Pre-set to 2018-01-01 → 2026-05-31. |
| `TIMEFRAMES` | Dictionary of timeframes to fetch. Remove any lines you don't need. |
| `MT5_LOGIN` | Leave as `0` to use whatever account is already logged into the open terminal. |
| `OUTPUT_DIR` | Folder where CSV files are saved. Created automatically if it doesn't exist. |

### Switching to tick mode

Change one line in the config:

```python
MODE = "tick"
```

Tick data for the full date range is saved as a single CSV.

---

## Output

**OHLC mode** — one CSV per timeframe, named like:
```
mt5_data/EURUSD_H1_20180101_20260531.csv
```
Columns: `datetime, open, high, low, close, tick_vol, real_vol, spread`

**Tick mode** — one CSV for the full range, named like:
```
mt5_data/EURUSD_TICK_20180101_20260531.csv
```
Columns: `datetime, time_msc, bid, ask, last, volume, flags`

All timestamps are **UTC**.

---

## What to Expect

- **OHLC** runs in seconds to a couple of minutes depending on how many timeframes
  and how much history the broker provides.
- **Tick data** for a multi-year range can be very large (hundreds of MB to several GB
  for liquid pairs like EURUSD). Allow significant time and disk space.
- Bar counts will vary: M1 from 2018 to mid-2026 is roughly 2–3 million rows;
  MN1 for the same period is about 100 rows.

---

## Limitations & Caveats

- **Windows only.** The `MetaTrader5` package does not work on any other OS.
- **History depth is broker-dependent.** Not all brokers store data back to 2018 for
  all timeframes, especially exotic instruments or very short timeframes like M2/M3.
- **All times are UTC.** MT5 internally stores bar open times in UTC regardless of
  the broker's display timezone. The script preserves this.
- **`real_volume` is usually 0 for OTC/Forex** because true exchange volume is not
  available. `tick_vol` (number of price updates per bar) is used instead.
- **Tick history is sparse.** MT5 tick storage is not guaranteed to be complete for
  periods years in the past. Gaps are normal.
- **Do not run while actively trading.** The script only reads data and doesn't place
  orders, but loading large history can temporarily affect terminal performance.
- **M2, M3, M4, M6, M10, M12, M20, H2, H3, H6, H8, H12 are MT5-only** — these
  timeframes do not exist in MT4. They are fully supported by the Python API.
- **The script has no retry logic.** If a timeframe returns no data, it prints a
  warning and continues. Re-run after fully loading the chart history in MT5.
