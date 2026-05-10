# Post-Migration Optimization for Home Assistant

Now that your historical numeric data is safely stored in InfluxDB, you can optimize your Home Assistant `recorder` configuration. The goal is to make the "active" database (MariaDB or SQLite) as lean and fast as possible, leaving the "heavy lifting" of long-term history to InfluxDB.

## 1. Reduce Retention Period

By default, Home Assistant keeps 10 days of history. Since you now have years of data in InfluxDB, you can safely reduce this to 7 days (or even less). This will:
- **Improve UI Performance:** The "Logbook" and "History" tabs will load much faster.
- **Reduce Disk Usage:** Your database file size will shrink significantly.
- **Speed Up Backups:** Smaller databases mean faster Home Assistant backups.

Update your `configuration.yaml`:

```yaml
recorder:
  purge_keep_days: 7
  # Optional: Auto-purge every night at 4 AM
  auto_purge: true
```

---

## 2. Moving Away from the NAS (Optional)

If your primary goal was to stop using the slow MariaDB on your NAS, you have two main options:

### Option A: Move MariaDB to Fast Storage
If you have a fast machine (like the one where you ran the migration), you can keep using MariaDB but host it there instead of the NAS. 

Update your `db_url` in `configuration.yaml`:
```yaml
recorder:
  db_url: mysql://user:password@FAST_MACHINE_IP:3306/ha?charset=utf8mb4
  purge_keep_days: 7
```

### Option B: Switch back to SQLite (Recommended for NVMe)
If you moved Home Assistant itself to a machine with fast NVMe storage, the default **SQLite** database is often faster and much easier to manage than an external MariaDB.

1.  **Comment out** the `db_url` in your `recorder` config.
2.  **Restart Home Assistant.** It will automatically create a new `home-assistant_v2.db` file in your config folder.
3.  **Note:** This starts a *fresh* short-term history. Your long-term history is still safe in InfluxDB.

---

## 3. What about Long-Term Statistics?

Home Assistant has a built-in "Long-term Statistics" feature that is separate from the `recorder` state history. 
- Even if you set `purge_keep_days: 7`, Home Assistant will still keep hourly/daily min/max/mean statistics for your sensors indefinitely in its internal database.
- These statistics are used for the built-in "Energy" dashboard and "Statistics Graph" cards.
- **InfluxDB** remains your primary tool for high-resolution, raw-data analysis and advanced Grafana dashboards.

## Summary of the "Lean" Setup
With this setup, your Home Assistant environment is optimized for both speed and depth:
1.  **MariaDB/SQLite:** Holds the last 7 days of "raw" state data for the UI.
2.  **HA Statistics:** Holds indefinite "min/max/avg" hourly data for native HA cards.
3.  **InfluxDB:** Holds your entire history of raw numeric data for advanced analysis.
