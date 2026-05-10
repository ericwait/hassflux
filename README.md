# Home Assistant Data Migration (MariaDB to InfluxDB)

A robust, professional tool for migrating Home Assistant numeric sensor data from a MariaDB instance to an InfluxDB v2 instance.

## Features

- **Professional Packaging:** Installable as a Python package.
- **Modern CLI:** Powered by Typer with support for batching and progress management.
- **Type-Safe Config:** Uses Pydantic Settings for robust environment variable handling.
- **Resilient:** Auto-recovers from database connection drops.
- **Efficient:** Uses asynchronous InfluxDB writes and optimized MariaDB queries.

## Installation

### Prerequisites

- Python 3.9 or higher.
- A running MariaDB instance (with Home Assistant data).
- A running InfluxDB v2 instance.

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ericwait/hassflux.git
   cd hassflux
   ```

2. **Install the package:**
   ```bash
   pip install .
   ```
   *(Or for development: `pip install -e ".[dev]"`)*

3. **Configure the environment:**
   Copy the example environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your MariaDB and InfluxDB settings
   ```

## The Use Case: High-Performance Migration

This tool was designed for a specific, common Home Assistant performance bottleneck:

1.  **The Problem:** Home Assistant is running its long-term state data on a MariaDB instance hosted on a NAS (e.g., Synology/QNAP) with spinning disks. Performing the millions of queries required for a full migration over the network against slow HDDs is extremely slow and can impact NAS performance.
2.  **The Goal:** Move that data to a high-performance InfluxDB v2 instance running on a faster machine with NVMe storage.
3.  **The Solution:**
    *   **Backup & Localize:** Perform a `mysqldump` of the MariaDB `states` and `states_meta` tables on the NAS. This is a sequential read operation that HDDs handle well.
    *   **Local MariaDB:** Restore that dump to a local MariaDB Docker container running on the same NVMe-backed machine as your InfluxDB.
    *   **High-Speed Migration:** Run `hassflux` against the local MariaDB. This eliminates network latency and leverages NVMe IOPS, increasing migration speed from ~1-2k pts/sec to 8k+ pts/sec.

*Note: If your MariaDB is already running on fast hardware (e.g., an SSD-backed NUC or Mini PC), you can bypass the backup/restore step and run `hassflux` directly against your production DB.*

## Configuration Guide

Hassflux uses a "pull-based" migration strategy. It looks at your **active** InfluxDB data to decide what to migrate from the past.

### 1. Match Your Entities
The `data/` directory contains template files to help you map your MariaDB data to the correct InfluxDB measurements.

*   **`data/entity_mapping.json.example`**: Home Assistant stores states in InfluxDB using the unit of measurement as the table name (e.g., `°F`, `%`, `V`). Map your entity IDs to their respective units here.
*   **`data/friendly_names.json.example`**: (Optional) If you want your historical data to have the same `friendly_name` tags as your live data, provide the mapping here.

### 2. Environment Variables
Copy `.env.example` to `.env` and configure your credentials.

```bash
# MariaDB (Point this to your local NVMe-backed restore for best speed)
MARIADB_HOST=127.0.0.1
MARIADB_PORT=3306
MARIADB_USER=your_user
MARIADB_PASS=your_pass
MARIADB_DB=ha

# InfluxDB
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your_token
INFLUX_ORG=homeassistant
INFLUX_BUCKET=homeassistant
```

## Documentation

-   [**Step-by-Step Walkthrough**](docs/walkthrough.md): The recommended path for high-performance migration.
-   [**Home Assistant Setup**](docs/home_assistant_setup.md): How to configure HA for clean data and use the "Warm-up" strategy.
-   [**Post-Migration Optimization**](docs/post_migration_optimization.md): How to slim down your Home Assistant database once migration is complete.
-   [**Migration Strategy**](docs/MIGRATION_SUMMARY.md): A deep dive into the architecture and logic.

## Usage

To start or resume the migration:
```bash
hassflux migrate
```

### Options

- `--batch-size` / `-b`: Override the batch size from config.
- `--reset`: Reset migration progress and start from `state_id = 0`.
- `--help`: Show all available commands and options.

```bash
hassflux migrate --batch-size 10000 --reset
```

## Architecture

- **State Tracking:** Uses `data/migration_progress.txt` to keep track of the last successful `state_id`.
- **Filtering:** Only migrates entities that are already present in the target InfluxDB bucket to prevent database pollution.
- **Data Precision:** Mirrors Home Assistant's microsecond precision for timestamps.

## Data Schema

To ensure perfect continuity in Grafana, `hassflux` mirrors the exact schema used by the official Home Assistant InfluxDB integration:

-   **Measurement:** The unit of measurement (e.g., `°F`, `%`, `kWh`, or `units` if no unit is defined).
-   **Tags:**
    -   `domain`: Always set to `sensor`.
    -   `entity_id`: The stripped entity ID (e.g., `living_room_temperature`).
    -   `source`: Always set to `HA`.
    -   `friendly_name`: (Optional) Custom name from your mapping file.
-   **Fields:**
    -   `value`: The numeric state (stored as a float).
-   **Precision:** Microseconds (`US`).

## Tips for Success

-   **Back Up First:** While `hassflux` only performs `SELECT` queries on your MariaDB, always ensure you have a fresh backup of your data before performing large migrations.
-   **Batch Size:** The default `50000` is optimized for systems with 16GB+ RAM. If you encounter memory issues, reduce the `--batch-size` to `10000` or `20000`.
-   **InfluxDB Permissions:** Ensure your InfluxDB token has **write** access to the target bucket and **read** access (for the pre-flight active sensor check).

## Frequently Asked Questions

**Q: Does this migrate binary sensors or attributes?**
A: No. `hassflux` is specifically designed for numeric sensor data to preserve long-term historical trends (temperature, energy, etc.).

**Q: Can I run this while Home Assistant is running?**
A: Yes. However, if you are following the "High-Performance" path (using a local dump), your migrated data will only be as current as your backup. You can run `hassflux` multiple times to "catch up."

**Q: How do I handle entities that changed units over time?**
A: Home Assistant writes to a measurement based on the *current* unit. You should map your historical data to match the measurement currently being used in your InfluxDB.

## Development

Running linting and type checking:
```bash
ruff check src/
mypy src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details on how to get involved.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
