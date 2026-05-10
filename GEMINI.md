# Home Assistant Data Migration (MariaDB to InfluxDB)

This project provides a robust, resilient tool for migrating Home Assistant numeric sensor data from a MariaDB instance (typically on a NAS/Synology) to an InfluxDB instance (typically on high-performance storage like NVMe).

## Project Overview

- **Purpose:** Migrate 41m+ records of Home Assistant state data to InfluxDB.
- **Source:** MariaDB (v2 schema, `states` and `states_meta` tables).
- **Destination:** InfluxDB v2.
- **Key Features:**
    - **Progress Persistence:** Resumes from the last successful `state_id` using `migration_progress.txt`.
    - **Auto-Recovery:** Indefinitely attempts to reconnect to MariaDB if the network or database drops.
    - **Performance:** Uses asynchronous writes to InfluxDB and batch processing to handle high volume.
    - **Filtering:** Only migrates `sensor.*` entities with numeric states.

## Getting Started

### Prerequisites

- [Mamba](https://mamba.readthedocs.io/en/latest/) or Conda
- Project environment:
  ```bash
  # Create the environment if it doesn't exist
  mamba env create -f environment.yml
  
  # Activate the environment
  mamba activate influx-migrate
  ```

### Configuration

Settings are managed via environment variables (typically in a `.env` file) and parsed using Pydantic Settings in `src/hassflux/config.py`.

### Running the Migration

```bash
pip install .
hassflux migrate
```

The CLI provides real-time progress, including the last processed `state_id` and the points-per-second migration rate.

### Tools

The CLI also includes auxiliary tools:
```bash
hassflux tools inspect-influx
hassflux tools inspect-db
```

## Architecture & Conventions

- **State Tracking:** The `state_id` from MariaDB's `states` table is used as the primary pointer for progress.
- **Robustness:** The script handles `OperationalError` and `InterfaceError` by re-establishing the database connection.
- **Data Model:**
    - Measurement: `units`
    - Tag: `entity_id`
    - Tag: `source="HA"`
    - Field: `value` (numeric)
    - Time: `last_updated_ts` (seconds precision)

## Maintenance

- To reset the migration, delete `migration_progress.txt`.
- To change the starting point, manually edit `migration_progress.txt` with the desired `state_id`.
