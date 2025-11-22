# Trading Manager CLI

`trading_manager_cli.py` replaces the previous stock fetcher scripts with a single command-line utility that downloads historical OHLC pricing and optional fundamentals data for any list of tickers.

## Overview

- **Pricing data**: daily Open/High/Low/Close plus volume (and dividends/adj close when available).
- **Current fundamentals** (`--fundamentals`): trailing P/E, EPS, ROE, and dividend yield pulled from Yahoo Finance key stats.
- **Quarterly fundamentals** (`--quarterly-fundamentals`): every column from `yahooquery`'s quarterly income statement (BasicEPS, TotalRevenue, GrossProfit, NetIncome, etc.) merged onto the daily rows with backward-filling.
- **Logging**: `--log-level` controls verbosity (`INFO` by default, `DEBUG` surfaces Yahoo-related traffic for troubleshooting).

## Setup

1. Create a virtual environment (recommended):

```bash
python -m venv .venv
```

2. Activate it:

- On Windows PowerShell:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- On Windows CMD:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## CLI Usage

The CLI requires `--input` (CSV with a `ticker` column) and `--output`. Dates default to `2023-01-01` through today.

```bash
python trading_manager_cli.py \
  --input stocks.csv \
  --output prices.csv \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --fundamentals \
  --quarterly-fundamentals \
  --log-level DEBUG
```

- `--fundamentals`: adds P/E, EPS, ROE, and Dividend Yield columns (repeat horizontally per ticker).
- `--quarterly-fundamentals`: merges every quarterly income-statement metric and backward-fills values so the most recent quarter applies to subsequent trading days.
- `--log-level`: specify `DEBUG`, `INFO`, `WARNING`, or `ERROR` for more/less console noise.

## Input & Output Format

- Input CSV must include a `ticker` column. Example:
  ```csv
  ticker
  AAPL
  GOOGL
  MSFT
  ```
- Output CSV always contains: `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`, `Volume`.
- Enabling `--fundamentals` appends `P/E`, `EPS`, `ROE`, and `Dividend_Yield` columns.
- Enabling `--quarterly-fundamentals` adds all quarterly-income-statement columns (BasicEPS, TotalRevenue, GrossProfit, NetIncome, OperatingIncome, ResearchAndDevelopment, etc.) merged onto the daily data.

## Examples

1. **Daily OHLC only**

   ```bash
   python trading_manager_cli.py --input stocks.csv --output prices.csv
   ```

2. **Add current fundamentals**

   ```bash
   python trading_manager_cli.py --input stocks.csv --output fundamentals.csv --fundamentals
   ```

3. **Include every quarterly metric + debug logging**

   ```bash
   python trading_manager_cli.py \
     --input stocks.csv \
     --output prices_with_quarters.csv \
     --fundamentals \
     --quarterly-fundamentals \
     --log-level DEBUG
   ```

## Troubleshooting

- If no rows are written, check your tickers/date range and inspect the log output for Yahoo rate-limiting or connectivity errors.
- The CLI adds one day to the provided `--end` date internally so that the final trading date is included in the range.

## Additional Notes

- Historical files `stock_fetcher.py` and `stock_fetcher_v2.py` remain in the repo for reference but `trading_manager_cli.py` is the consolidated version.
- The tool depends on Yahoo Finance via `yahooquery`; any breaking changes upstream may require updates.
- No automated tests are provided; validate manually by running the CLI with a short ticker list and inspecting the resulting CSV.

## License & Attribution

- This tool is built with `pandas` and `yahooquery` and is meant for personal/educational use. Respect Yahoo Finance's terms when accessing their data.