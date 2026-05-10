# Step-by-Step Migration Walkthrough

This guide provides a detailed end-to-end walkthrough of migrating your Home Assistant data using the "High-Performance" path.

## Prerequisites
- **Home Assistant:** Configured to write to InfluxDB (see [Home Assistant Setup](home_assistant_setup.md)).
- **Warm-up:** Your InfluxDB bucket must already contain some data for the sensors you wish to migrate.
- **Access:** Access to your Home Assistant MariaDB (e.g., via SSH or a database client).
- **Docker:** Installed on your "fast" machine (the one with NVMe).
- **Python:** Python 3.9+ installed.

---

## Step 1: Export Data from NAS
First, we need to get the data off the slow NAS disks. We only need the two tables that contain state history.

1.  **Run the dump command:**
    ```bash
    mysqldump -h YOUR_NAS_IP -P YOUR_PORT -u YOUR_USER -p'YOUR_PASSWORD' \
    --single-transaction --quick --skip-ssl \
    ha states states_meta > ha_backup.sql
    ```
2.  **Transfer the file:** Move `ha_backup.sql` to your fast machine (e.g., using `scp` or `rsync`).

## Step 2: Set Up Local MariaDB
Running a local MariaDB container ensures that `hassflux` can perform the millions of required queries with zero network latency and maximum disk speed.

1.  **Start the container:**
    ```bash
    docker run --name hassflux-mariadb \
      -e MARIADB_ROOT_PASSWORD=password \
      -e MARIADB_DATABASE=ha \
      -p 3306:3306 -d mariadb:latest
    ```
2.  **Restore the data:**
    ```bash
    mysql -h 127.0.0.1 -u root -ppassword ha < ha_backup.sql
    ```

## Step 3: Configure Hassflux
1.  **Clone & Install:**
    ```bash
    git clone https://github.com/ericwait/hassflux.git
    cd hassflux
    pip install .
    ```
2.  **Environment Setup:**
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and set `MARIADB_HOST=127.0.0.1` and `MARIADB_PORT=3306`. Fill in your InfluxDB v2 credentials.

3.  **Entity Mapping:**
    Ensure `data/entity_mapping.json` (copied from `.example`) contains the mappings for the sensors you want to migrate.

## Step 4: Run the Migration
1.  **Test the connection:**
    ```bash
    hassflux tools inspect-db
    ```
2.  **Start migrating:**
    ```bash
    hassflux migrate
    ```

## Step 5: Verify
Once complete, use the audit tool to verify your InfluxDB data:
```bash
hassflux tools audit
```
Check your Grafana dashboards—you should see a seamless transition between your historical data and live data.

---

## Step 6: Cleanup (Optional)
Once you are satisfied with the migration, you can remove the local MariaDB container and the SQL dump:
```bash
docker rm -f hassflux-mariadb
rm ha_backup.sql
```
