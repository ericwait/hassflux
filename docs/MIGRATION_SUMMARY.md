# Home Assistant Data Migration: MariaDB to InfluxDB

## 1. Project Objective
To migrate 41 million+ historical numeric sensor records from a live Home Assistant MariaDB instance to an InfluxDB v2 instance. The primary goal is to ensure a **seamless, indistinguishable transition** where historical data and live data merge into a single, continuous timeline without duplicates or schema fragmentation.

## 2. The Strategy: "The Clean Mirror"

### Phase 1: InfluxDB Optimization (The Clean Slate)
Instead of migrating everything, we transitioned to a "Quality over Quantity" approach.
- **Clean Sweep:** Wiped existing InfluxDB data to remove historical "noise" (strings, system states, and unformatted sensors).
- **HA Filter Refinement:** Updated `configuration.yaml` to exclude non-numeric domains (`sun`, `weather`, `binary_sensor`) and messy system sensors.
- **Unified Schema:** Enforced a schema where only sensors with units (e.g., `°F`, `%`, `V`) are stored, using the unit as the measurement name.

### Phase 2: Data Localization (The Speed Boost)
To overcome network latency and hardware bottlenecks on the Synology NAS:
- **Targeted Backup:** Exported only the `states` and `states_meta` tables from the live MariaDB.
- **Local Restore:** Restored the data to a local MariaDB Docker instance on the Mac (running on NVMe storage). This increased processing speed from ~2k pts/sec to an estimated 5k-8k pts/sec.

### Phase 3: Perfect Parity (The Pull-Based Migration)
To ensure the migration is 100% indistinguishable from live data:
- **Dynamic Allow-list:** The migration script now queries InfluxDB at startup to see exactly which `entity_id` tags Home Assistant is currently writing. It **only** migrates history for these active sensors.
- **Precision Alignment:** Synchronized timestamp precision to **Microseconds (US)** to match the native Home Assistant InfluxDB integration.
- **Tag Cloning:** Mirrored the exact tag set used by HA: `domain`, `entity_id`, `friendly_name`, and `source: HA`.

## 3. Technical Implementation
- **Security:** Moved all credentials into a centralized `.env` file, loaded via a `config.py` module.
- **Robustness:** Integrated automated reconnection logic for both MariaDB and InfluxDB.
- **Verification:** Integrated audit tools (`hassflux tools audit`, `hassflux tools inspect-influx`) to verify data quality before and after migration.

## 4. Expected Outcome
A lean, professional-grade InfluxDB database that provides:
1. **Perfect Continuity:** Dashboards in Grafana will show no break or "triplicate" entries at the point where historical data ends and live data begins.
2. **Reduced Storage:** By filtering out "noise," the database remains highly performant and easy to back up.
3. **Zero Maintenance:** The "Pull-based" migration logic ensures that if you add a new sensor to HA, the migration script will automatically include its history on the next run.

---
*Status: Ready for Final Execution*
