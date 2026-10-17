import pandas as pd

# Bluebikes source column -> workshop column
COLUMN_MAP = {
    "ride_id": "trip_id",
    "started_at": "started_at",
    "ended_at": "ended_at",
    "start_station_name": "start_station",
    "end_station_name": "end_station",
}


def transform_trips(raw: pd.DataFrame) -> pd.DataFrame:
    """Select five Bluebikes fields, rename them, and add trip duration.

    No validation happens here yet. Data quality rules are a live-workshop exercise.
    """
    trips = raw[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)
    trips["started_at"] = pd.to_datetime(trips["started_at"])
    trips["ended_at"] = pd.to_datetime(trips["ended_at"])
    trips["duration_minutes"] = (
        (trips["ended_at"] - trips["started_at"]).dt.total_seconds() / 60
    ).round(2)
    return trips
