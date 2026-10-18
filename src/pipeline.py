"""Starter pipeline: read one day of Bluebikes trips, transform, load to Snowflake.

Run from the repository root:
    python -m src.pipeline
"""

from pathlib import Path

import pandas as pd

from src.load import SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, TABLE, load_to_snowflake
from src.transform import transform_trips

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "bluebikes_trips_2024_03_28.csv"


def main() -> None:
    raw = pd.read_csv(CSV_PATH, dtype={"ride_id": str})
    print(f"Read {len(raw):,} rows from {CSV_PATH.name}")

    trips = transform_trips(raw)
    inserted = load_to_snowflake(trips)

    print(
        f"Loaded {inserted:,} rows into {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{TABLE}"
    )
    print("Note: every run appends again. We fix that during the workshop.")


if __name__ == "__main__":
    main()
