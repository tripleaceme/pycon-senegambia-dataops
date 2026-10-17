import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

TABLE = "BIKE_TRIPS"


def load_to_snowflake(trips: pd.DataFrame, config: dict) -> int:
    """Create BIKE_TRIPS if needed and append the trips. Returns rows inserted."""
    connection = snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        password=config["password"],
        warehouse=config["warehouse"],
        database=config["database"],
        schema=config["schema"],
        role=config.get("role") or None,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE} (
                    TRIP_ID VARCHAR,
                    STARTED_AT TIMESTAMP_NTZ,
                    ENDED_AT TIMESTAMP_NTZ,
                    START_STATION VARCHAR,
                    END_STATION VARCHAR,
                    DURATION_MINUTES FLOAT
                )
            """)
        success, _, inserted, _ = write_pandas(
            connection,
            trips.rename(columns=str.upper),
            TABLE,
            # Without this, pandas timestamps can arrive in Snowflake as invalid dates.
            use_logical_type=True,
        )
        if not success:
            raise RuntimeError("Snowflake reported a failed load")
        return inserted
    finally:
        connection.close()
