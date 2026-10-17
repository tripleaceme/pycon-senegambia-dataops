"""Instructor helper: extract one real day of Bluebikes trips.

Downloads an official monthly archive from the Bluebikes public bucket
(https://s3.amazonaws.com/hubway-data/index.html), keeps every ride that
started on the chosen date, and writes it to data/ unchanged: same columns,
same values, same order as the source file. Nothing is generated or sampled.

Participants do not need to run this. The repository already contains the file.

Usage:
    python scripts/dowload_data.py                      # 2026-01-01 (default)
    python scripts/dowload_data.py --date 2024-04-10    # any day with a published archive
"""

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

BUCKET = "https://s3.amazonaws.com/hubway-data"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--date", default="2026-01-01", help="Trip start date, YYYY-MM-DD"
    )
    args = parser.parse_args()

    day = pd.Timestamp(args.date)
    source = f"{BUCKET}/{day:%Y%m}-bluebikes-tripdata.zip"
    print(f"Downloading {source}")
    with urllib.request.urlopen(source, timeout=300) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    names = [
        n
        for n in archive.namelist()
        if n.endswith(".csv") and not n.startswith("__MACOSX/")
    ]
    if len(names) != 1:
        raise RuntimeError(f"Expected one CSV in the archive, found {names}")

    # Read everything as text so values are written back exactly as published.
    with archive.open(names[0]) as f:
        month = pd.read_csv(f, dtype=str, keep_default_na=False)

    rides = month[month["started_at"].str.startswith(args.date)]
    if rides.empty:
        raise RuntimeError(f"No rides started on {args.date}")

    output = DATA_DIR / f"bluebikes_trips_{day:%Y_%m_%d}.csv"
    DATA_DIR.mkdir(exist_ok=True)
    rides.to_csv(output, index=False)
    print(f"Saved {len(rides):,} real Bluebikes rides from {args.date} to {output}")


if __name__ == "__main__":
    main()
