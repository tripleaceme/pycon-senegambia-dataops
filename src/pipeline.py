"""Starter pipeline: read one day of Bluebikes trips, transform, load to Snowflake.

Run from the repository root:
    python -m src.pipeline
"""

import json
from pathlib import Path

import pandas as pd

from src.load import TABLE, load_to_snowflake
from src.transform import transform_trips

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "local_config.json"
CSV_PATH = ROOT / "data" / "bluebikes_trips_2024_03_28.csv"


def main() -> None:
    if not CONFIG_PATH.exists():
        raise SystemExit(
            "local_config.json not found. Copy local_config.example.json to "
            "local_config.json and fill in your Snowflake details."
        )
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    raw = pd.read_csv(CSV_PATH, dtype={"ride_id": str})
    print(f"Read {len(raw):,} rows from {CSV_PATH.name}")

    trips = transform_trips(raw)
    inserted = load_to_snowflake(trips, config)

    print(
        f"Loaded {inserted:,} rows into {config['database']}.{config['schema']}.{TABLE}"
    )
    print("Note: every run appends again. We fix that during the workshop.")


if __name__ == "__main__":
    main()
