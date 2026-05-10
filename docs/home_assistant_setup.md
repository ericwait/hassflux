# Home Assistant Setup for Hassflux

To get the most out of Hassflux, your Home Assistant InfluxDB integration should be configured to produce clean, numeric-only data. This ensures that your historical migration and your live data share the same schema and quality standards.

## 1. Official Documentation
First, ensure you have the [official InfluxDB integration](https://www.home-assistant.io/integrations/influxdb/) set up and working in Home Assistant.

---

## 2. Recommended `configuration.yaml`

We recommend a "Quality over Quantity" approach to your InfluxDB data. This reduces database noise and makes your dashboards faster.

Add or update the `influxdb:` section in your `configuration.yaml`:

```yaml
influxdb:
  api_version: 2
  ssl: false
  host: YOUR_INFLUX_IP
  port: 8086
  token: YOUR_TOKEN
  organization: homeassistant
  bucket: homeassistant
  
  # --- Optimization Settings ---
  # Only write numeric values to save space and ensure compatibility
  include_attributes: false
  
  # Filter domains to only include numeric sensors
  include:
    domains:
      - sensor
    # Alternatively, use an allow-list for specific entities
    # entities:
    #   - sensor.living_room_temperature
    
  # Exclude domains that are typically non-numeric or "noisy"
  exclude:
    domains:
      - automation
      - updater
      - person
      - zone
      - sun
      - weather
      - group
```

---

## 3. The "Warm-up" Phase (Crucial!)

Hassflux uses a **"Pull-based" allow-list strategy**. Before it migrates any historical data, it queries your InfluxDB bucket to see which sensors are currently reporting data.

### Why do we do this?
- **Prevents Pollution:** It ensures we don't migrate thousands of "dead" or irrelevant entities from your MariaDB history that you no longer care about.
- **Auto-Discovery:** It automatically finds the correct `measurement` name (the unit) for each sensor.

### How to "Warm up":
1.  **Configure InfluxDB** in Home Assistant as shown above.
2.  **Restart Home Assistant** to apply the changes.
3.  **Wait:** Let Home Assistant run for a few hours (or at least long enough for every sensor you care about to report its state at least once).
4.  **Verify:** You can use `hassflux tools inspect-influx` to see the sensors being discovered.

Once your desired sensors appear in InfluxDB, **Hassflux is ready to migrate their history.**
