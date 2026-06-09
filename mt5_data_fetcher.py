"""
MT5 Data Fetcher
================
Fetches OHLC (candlestick) or Tick data from a running MetaTrader 5 terminal
and saves each timeframe (or tick batch) to its own CSV file.

Switch between modes by setting MODE = "ohlc" or MODE = "tick" below.
All other settings are also configured in the CONFIG section.
"""

import os
import sys
from datetime import datetime, timezone

import MetaTrader5 as mt5
import pandas as pd

# ============================================================
#  CONFIGURATION  —  edit everything here, nowhere else
# ============================================================

# --- Connection (leave empty strings to use the already-logged-in terminal) ---
MT5_LOGIN = 0  # account number, e.g. 12345678  (0 = skip)
MT5_PASSWORD = ""  # account password
MT5_SERVER = ""  # broker server name, e.g. "BrokerName-Demo"

# --- Instrument ---
SYMBOL = "#SOLUSDr"

# --- Mode: "ohlc" (default) or "tick" ---
MODE = "ohlc"

# --- Date range (UTC) ---
DATE_FROM = datetime(2018, 1, 1, tzinfo=timezone.utc)
DATE_TO = datetime(2026, 5, 31, 23, 59, 59, tzinfo=timezone.utc)

# --- OHLC: timeframes to fetch ---
#     Remove any entry you don't need.
TIMEFRAMES = {
    "MN1": mt5.TIMEFRAME_MN1,
    "W1": mt5.TIMEFRAME_W1,
    "D1": mt5.TIMEFRAME_D1,
    "H12": mt5.TIMEFRAME_H12,
    "H8": mt5.TIMEFRAME_H8,
    "H6": mt5.TIMEFRAME_H6,
    "H4": mt5.TIMEFRAME_H4,
    "H3": mt5.TIMEFRAME_H3,
    "H2": mt5.TIMEFRAME_H2,
    "H1": mt5.TIMEFRAME_H1,
    "M30": mt5.TIMEFRAME_M30,
    "M20": mt5.TIMEFRAME_M20,
    "M15": mt5.TIMEFRAME_M15,
    "M12": mt5.TIMEFRAME_M12,
    "M10": mt5.TIMEFRAME_M10,
    "M6": mt5.TIMEFRAME_M6,
    "M5": mt5.TIMEFRAME_M5,
    "M4": mt5.TIMEFRAME_M4,
    "M3": mt5.TIMEFRAME_M3,
    "M2": mt5.TIMEFRAME_M2,
    "M1": mt5.TIMEFRAME_M1,
}

# --- Tick: which ticks to retrieve ---
#     Options: mt5.COPY_TICKS_ALL | mt5.COPY_TICKS_INFO | mt5.COPY_TICKS_TRADE
TICK_FLAGS = mt5.COPY_TICKS_ALL

# --- Output ---
OUTPUT_DIR = "mt5_data"  # folder created next to this script
CSV_SEPARATOR = ","

# ============================================================
#  END OF CONFIGURATION
# ============================================================


def connect() -> bool:
    """Initialise and optionally log in to the MT5 terminal."""
    if not mt5.initialize():
        print(f"[ERROR] mt5.initialize() failed — {mt5.last_error()}")
        return False

    if MT5_LOGIN:
        auth = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
        if not auth:
            print(f"[ERROR] mt5.login() failed — {mt5.last_error()}")
            mt5.shutdown()
            return False

    info = mt5.terminal_info()
    print(f"[OK] Connected  |  terminal: {info.name}  |  build: {info.build}")
    return True


def check_symbol(symbol: str) -> bool:
    """Verify the symbol exists and is visible."""
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"[ERROR] Symbol '{symbol}' not found — {mt5.last_error()}")
        return False
    if not info.visible:
        mt5.symbol_select(symbol, True)
    return True


def fetch_ohlc(
    symbol: str, tf_name: str, tf_const: int, date_from: datetime, date_to: datetime
) -> pd.DataFrame | None:
    """Fetch OHLC bars for one timeframe and return a DataFrame."""
    rates = mt5.copy_rates_range(symbol, tf_const, date_from, date_to)
    if rates is None or len(rates) == 0:
        print(f"  [{tf_name}] No data returned — {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.rename(
        columns={
            "time": "datetime",
            "tick_volume": "tick_vol",
            "real_volume": "real_vol",
        },
        inplace=True,
    )
    return df[
        ["datetime", "open", "high", "low", "close", "tick_vol", "real_vol", "spread"]
    ]


def fetch_ticks(
    symbol: str, date_from: datetime, date_to: datetime, flags: int
) -> pd.DataFrame | None:
    """Fetch all ticks in the date range and return a DataFrame."""
    ticks = mt5.copy_ticks_range(symbol, date_from, date_to, flags)
    if ticks is None or len(ticks) == 0:
        print(f"  [TICK] No data returned — {mt5.last_error()}")
        return None

    df = pd.DataFrame(ticks)
    # time_msc is millisecond timestamp; derive a human-readable column
    df["datetime"] = pd.to_datetime(df["time_msc"], unit="ms", utc=True)
    df.drop(columns=["time"], inplace=True)  # keep time_msc for precision
    return df[["datetime", "time_msc", "bid", "ask", "last", "volume", "flags"]]


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False, sep=CSV_SEPARATOR)


def run_ohlc(symbol: str) -> None:
    print(f"\n[OHLC mode]  Symbol: {symbol}  |  {len(TIMEFRAMES)} timeframe(s)")
    print(f"Range: {DATE_FROM.date()} → {DATE_TO.date()}\n")

    out_dir = os.path.join(OUTPUT_DIR, symbol, "ohlc")
    os.makedirs(out_dir, exist_ok=True)
    success, skipped = 0, 0

    for tf_name, tf_const in TIMEFRAMES.items():
        df = fetch_ohlc(symbol, tf_name, tf_const, DATE_FROM, DATE_TO)
        if df is None:
            skipped += 1
            continue

        filename = f"{symbol}_{tf_name}_{DATE_FROM.strftime('%Y%m%d')}_{DATE_TO.strftime('%Y%m%d')}.csv"
        filepath = os.path.join(out_dir, filename)
        save_csv(df, filepath)
        print(f"  [{tf_name:>3}]  {len(df):>8,} bars  →  {filepath}")
        success += 1

    print(f"\nDone.  Saved: {success}  |  Skipped: {skipped}")


def run_tick(symbol: str) -> None:
    print(f"\n[TICK mode]  Symbol: {symbol}")
    print(f"Range: {DATE_FROM.date()} → {DATE_TO.date()}\n")

    out_dir = os.path.join(OUTPUT_DIR, symbol, "tick")
    os.makedirs(out_dir, exist_ok=True)

    df = fetch_ticks(symbol, DATE_FROM, DATE_TO, TICK_FLAGS)
    if df is None:
        print("No tick data retrieved. Exiting.")
        return

    filename = (
        f"{symbol}_TICK_{DATE_FROM.strftime('%Y%m%d')}_{DATE_TO.strftime('%Y%m%d')}.csv"
    )
    filepath = os.path.join(out_dir, filename)
    save_csv(df, filepath)
    print(f"  [TICK]  {len(df):>10,} ticks  →  {filepath}")
    print("\nDone.")


def main() -> None:
    if not connect():
        sys.exit(1)

    try:
        if not check_symbol(SYMBOL):
            sys.exit(1)

        if MODE.lower() == "tick":
            run_tick(SYMBOL)
        else:
            run_ohlc(SYMBOL)

    finally:
        mt5.shutdown()
        print("[INFO] MT5 connection closed.")


if __name__ == "__main__":
    main()