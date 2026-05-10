# MariaDB to InfluxDB Migration Recovery Plan

This plan outlines the steps to resume the migration of 41M+ records following a terminal reset and network instability.

## Phase 1: Stabilize & Dump
The primary goal is to get a local copy of the data to eliminate network latency and Synology disk bottlenecks.

1.  **Check Source:** Ensure the MariaDB container on the Synology (YOUR_NAS_IP:4408) is healthy and not under high CPU load.
2.  **Resilient Dump:** Run the dump command. If it fails midway, we will use a split approach or compression.
    ```bash
    # Standard dump (Tables: states, states_meta)
    mysqldump -h YOUR_NAS_IP -P 4408 -u YOUR_USER -p'YOUR_PASSWORD' \
    --single-transaction --quick --skip-ssl \
    ha states states_meta > ha_backup.sql
    ```

## Phase 2: Localize MariaDB (Docker)
By running MariaDB locally on your MacBook (NVMe), the migration speed will increase by 10x-20x.

1.  **Start Container:**
    ```bash
    docker run --name mariadb_local -e MARIADB_ROOT_PASSWORD=password \
    -e MARIADB_DATABASE=ha -e MARIADB_USER=YOUR_USER \
    -e MARIADB_PASSWORD=YOUR_PASSWORD -p 3306:3306 -d mariadb:latest
    ```
2.  **Import Data:**
    ```bash
    mysql -h 127.0.0.1 -u YOUR_USER -p'YOUR_PASSWORD' ha < ha_backup.sql
    ```

## Phase 3: Execute Migration
Using the optimized `hassflux` CLI.

1.  **Setup Environment:**
    ```bash
    pip install .
    ```
2.  **Configure:**
    Update your `.env` to point to `127.0.0.1:3306`.
3.  **Run:**
    ```bash
    hassflux migrate
    ```

## Troubleshooting
- **Dump hangs:** Try dumping tables separately (`states` first, then `states_meta`).
- **Memory issues:** The `batch_size` is configurable via CLI or `.env`.
- **Resuming:** The tool uses `data/migration_progress.txt`. Do not delete this file if you need to stop and start.
