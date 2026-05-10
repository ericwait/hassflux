import typer
from influxdb_client import InfluxDBClient
import pymysql
import json
import os
from datetime import datetime, timezone
import time
from pathlib import Path
from .config import settings
from .database import get_influx_client, get_mariadb_connection

tools_app = typer.Typer(help="Auxiliary tools for inspecting and verifying data.")

@tools_app.command()
def inspect_influx(
    minutes: int = typer.Option(15, help="Minutes of history to analyze.")
):
    """Analyze data from the last X minutes in InfluxDB."""
    client = get_influx_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r["_field"] == "value")
      |> group(columns: ["_measurement", "entity_id"])
      |> count()
      |> group()
      |> sort(columns: ["_value"], desc: true)
      |> limit(n: 50)
    '''
    
    typer.echo(f"Analyzing data from the last {minutes}m in '{settings.influx_bucket}'...")
    typer.echo(f"{'Count':<8} | {'Measurement':<20} | {'Entity ID'}")
    typer.echo("-" * 60)
    
    try:
        tables = query_api.query(query)
        found_any = False
        for table in tables:
            for record in table.records:
                found_any = True
                count = record.get_value()
                measurement = record.get_measurement()
                entity_id = record.values.get("entity_id", "N/A")
                typer.echo(f"{count:<8} | {str(measurement):<20} | {entity_id}")
        
        if not found_any:
            typer.echo("No data found. Is Home Assistant writing?")
            
    except Exception as e:
        typer.echo(f"Error analyzing data: {e}")
    finally:
        client.close()

@tools_app.command()
def inspect_db():
    """Check MariaDB statistics for Home Assistant states."""
    db = get_mariadb_connection()
    try:
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        typer.echo("Querying MariaDB for state statistics...")
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM states")
        total_states = cursor.fetchone()['count']
        
        cursor.execute("SELECT MIN(state_id) as min_id, MAX(state_id) as max_id FROM states")
        range_data = cursor.fetchone()
        
        typer.echo(f"Total States: {total_states:,}")
        typer.echo(f"ID Range: {range_data['min_id']} to {range_data['max_id']}")
        
    except Exception as e:
        typer.echo(f"Error querying database: {e}")
    finally:
        db.close()

@tools_app.command()
def discover_missing(
    mapping_file: Path = typer.Option(Path("data/entity_mapping.json"), help="Path to mapping JSON.")
):
    """Discover sensors in MariaDB that are not in the current mapping."""
    db = get_mariadb_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT entity_id FROM states_meta WHERE entity_id LIKE 'sensor.%'")
        all_entities = [row[0] for row in cursor.fetchall()]
        
        if mapping_file.exists():
            with open(mapping_file, "r") as f:
                current_mapping = json.load(f)
        else:
            current_mapping = {}
        
        typer.echo(f"Found {len(all_entities)} total sensor entities in MariaDB history.")
        
        missing = []
        for entity in all_entities:
            stripped = entity[7:] if entity.startswith('sensor.') else entity
            if stripped not in current_mapping:
                missing.append(entity)
        
        if missing:
            typer.echo(f"\n[!] Found {len(missing)} sensors in MariaDB that are NOT in your mapping:")
            for m in sorted(missing)[:50]:
                typer.echo(f"  - {m}")
            if len(missing) > 50:
                typer.echo(f"  ... and {len(missing)-50} more.")
        else:
            typer.echo("\n[+] Success: All sensors in MariaDB history are accounted for.")
    except Exception as e:
        typer.echo(f"Error: {e}")
    finally:
        db.close()

@tools_app.command()
def purge_influx():
    """Wipe all data from the configured InfluxDB bucket."""
    confirm = typer.confirm("Are you sure you want to PURGE ALL DATA from the bucket?")
    if not confirm:
        raise typer.Abort()

    client = get_influx_client()
    delete_api = client.delete_api()
    query_api = client.query_api()

    start = "1970-01-01T00:00:00Z"
    stop = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    typer.echo(f"Starting purge of bucket '{settings.influx_bucket}'...")
    
    try:
        m_query = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{settings.influx_bucket}")'
        tables = query_api.query(m_query)
        measurements = [record.get_value() for table in tables for record in table.records]
        
        if not measurements:
            typer.echo("No measurements found to delete.")
            return

        for i, m in enumerate(measurements):
            typer.echo(f"[{i+1}/{len(measurements)}] Deleting measurement: {m}...")
            predicate = f'_measurement="{m}"'
            delete_api.delete(start, stop, predicate, bucket=settings.influx_bucket, org=settings.influx_org)
        
        typer.echo("Purge complete.")
    except Exception as e:
        typer.echo(f"Error during purge: {e}")
    finally:
        client.close()

@tools_app.command()
def audit():
    """Perform an exhaustive audit of all entities in InfluxDB."""
    client = get_influx_client()
    query_api = client.query_api()

    query = f'''
    from(bucket: "{settings.influx_bucket}")
      |> range(start: 1970-01-01T00:00:00Z)
      |> filter(fn: (r) => r["_field"] == "value")
      |> group(columns: ["_measurement", "entity_id"])
      |> distinct(column: "entity_id")
      |> keep(columns: ["_measurement", "entity_id"])
      |> group()
      |> sort(columns: ["_measurement", "entity_id"])
    '''
    
    typer.echo(f"Performing exhaustive audit of all entities in '{settings.influx_bucket}'...")
    typer.echo(f"{'Measurement':<20} | {'Entity ID'}")
    typer.echo("-" * 60)
    
    try:
        tables = query_api.query(query)
        total_count = 0
        for table in tables:
            for record in table.records:
                total_count += 1
                measurement = record.get_measurement()
                entity_id = record.values.get("entity_id", "N/A")
                typer.echo(f"{str(measurement):<20} | {entity_id}")
        
        typer.echo("-" * 60)
        typer.echo(f"Total Unique Entities Found: {total_count}")
    except Exception as e:
        typer.echo(f"Error during audit: {e}")
    finally:
        client.close()
