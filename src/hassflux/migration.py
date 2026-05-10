import time
from typing import Dict, Any, List
import pymysql
from influxdb_client import Point, WritePrecision
from influxdb_client.client.write_api import ASYNCHRONOUS

from .config import settings
from .database import get_mariadb_connection, get_influx_client
from .utils import load_friendly_names, get_start_id, save_progress

def get_active_sensors(client) -> Dict[str, str]:
    """Queries InfluxDB for active sensors to use as an allow-list."""
    print("Pre-flight: Querying InfluxDB for active sensors...")
    query_api = client.query_api()
    
    query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: 1970-01-01T00:00:00Z)
      |> filter(fn: (r) => r["_field"] == "value")
      |> group(columns: ["_measurement", "entity_id"])
      |> last()
      |> group()
      |> keep(columns: ["_measurement", "entity_id"])
    '''
    
    try:
        tables = query_api.query(query)
        allow_list = {}
        for table in tables:
            for record in table.records:
                eid = record.values.get("entity_id")
                measurement = record.get_measurement()
                if eid and measurement:
                    allow_list[eid] = measurement
        return allow_list
    except Exception as e:
        print(f"Error querying active sensors: {e}")
        return {}

def run_migration(
    batch_size: int = settings.batch_size,
    reset_progress: bool = False
) -> None:
    """Main migration loop."""
    client = get_influx_client()
    
    active_sensors = get_active_sensors(client)
    if not active_sensors:
        print("\n[!] No active sensors found in InfluxDB.")
        client.close()
        return

    print(f"Found {len(active_sensors)} active sensors in InfluxDB.")
    
    friendly_names = load_friendly_names(settings.friendly_name_file)
    
    if reset_progress:
        last_state_id = 0
    else:
        last_state_id = get_start_id(settings.progress_file)
    
    write_api = client.write_api(write_options=ASYNCHRONOUS)
    db = get_mariadb_connection()

    print(f"Starting migration from state_id: {last_state_id}...")
    total_migrated = 0
    start_time = time.time()

    try:
        while True:
            try:
                cursor = db.cursor(pymysql.cursors.DictCursor)
                sql_query = """
                    SELECT s.state_id, sm.entity_id, s.state, s.last_updated_ts
                    FROM states s FORCE INDEX (PRIMARY)
                    JOIN states_meta sm ON s.metadata_id = sm.metadata_id
                    WHERE s.state_id > %s
                    ORDER BY s.state_id ASC
                    LIMIT %s;
                """
                cursor.execute(sql_query, (last_state_id, batch_size))
                rows = cursor.fetchall()
            except (pymysql.OperationalError, pymysql.InterfaceError) as e:
                print(f"\n[!] MariaDB connection lost: {e}. Reconnecting...")
                db = get_mariadb_connection()
                continue

            if not rows:
                print("\nMigration Complete!")
                break

            points_to_write = []
            for row in rows:
                full_entity_id = row['entity_id']
                # HA usually prefixes with 'sensor.' in MariaDB but not necessarily in Influx tags
                stripped_eid = full_entity_id[7:] if full_entity_id.startswith('sensor.') else full_entity_id
                
                if stripped_eid not in active_sensors:
                    continue
                
                measurement = active_sensors[stripped_eid]
                friendly_name = friendly_names.get(stripped_eid)

                try:
                    numeric_value = float(row['state'])
                except (ValueError, TypeError):
                    continue

                point = Point(measurement) \
                    .tag("domain", "sensor") \
                    .tag("entity_id", stripped_eid) \
                    .tag("source", "HA")
                
                if friendly_name:
                    point.tag("friendly_name", friendly_name)
                    
                point.field("value", numeric_value) \
                    .time(int(float(row['last_updated_ts']) * 1_000_000), WritePrecision.US)
                
                points_to_write.append(point)

            if points_to_write:
                write_api.write(bucket=settings.influx_bucket, record=points_to_write)

            total_migrated += len(points_to_write)
            last_state_id = rows[-1]['state_id']
            save_progress(settings.progress_file, last_state_id)

            elapsed = time.time() - start_time
            rate = total_migrated / elapsed if elapsed > 0 else 0
            print(f"[{time.strftime('%H:%M:%S')}] ID: {last_state_id} | Migrated: {total_migrated:,} | Rate: {rate:.2f} pts/sec")

    except KeyboardInterrupt:
        print(f"\nMigration paused. Progress saved at ID {last_state_id}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        write_api.flush()
        client.close()
        db.close()
        print("\nConnections closed.")
