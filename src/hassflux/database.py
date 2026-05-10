import time
import pymysql
from influxdb_client import InfluxDBClient
from .config import settings

def get_mariadb_connection():
    """Establishes and returns a connection to MariaDB with retry logic."""
    while True:
        try:
            return pymysql.connect(
                host=settings.mariadb_host,
                port=settings.mariadb_port,
                user=settings.mariadb_user,
                password=settings.mariadb_pass,
                database=settings.mariadb_db,
                connect_timeout=60
            )
        except Exception as e:
            print(f"Failed to connect to MariaDB: {e}. Retrying in 5s...")
            time.sleep(5)

def get_influx_client() -> InfluxDBClient:
    """Initializes and returns an InfluxDB client."""
    return InfluxDBClient(
        url=settings.influx_url,
        token=settings.influx_token,
        org=settings.influx_org,
        timeout=60000
    )
