import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# Snowflake connection details.
# Replace the placeholders with your own values, then run the pipeline.
# Do not commit this file once your password is in it.
SNOWFLAKE_ACCOUNT = "your_account_identifier"
SNOWFLAKE_USER = "your_username"
SNOWFLAKE_PASSWORD = "your_password"
SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
SNOWFLAKE_DATABASE = "DATAOPS_WORKSHOP"
SNOWFLAKE_SCHEMA = "PUBLIC"
SNOWFLAKE_ROLE = "ACCOUNTADMIN"

TABLE = "BIKE_TRIPS"


def load_to_snowflake(trips: pd.DataFrame) -> int:
    """Create BIKE_TRIPS if needed and append the trips. Returns rows inserted."""
    connection = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE,
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
