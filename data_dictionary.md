# Data Dictionary

## Station Information

| Field | Description |
|---|---|
| station_id | Unique monitoring station identifier |
| station_type | Lake, rainfall, or river station |
| latitude | Station latitude |
| longitude | Station longitude |
| elevation | Station elevation |
| sensor_status | Operational status |
| battery_percent | Remaining battery |
| last_transmission | Most recent data transmission |

## Hydrometeorological Data

| Field | Description |
|---|---|
| timestamp | Observation time |
| water_level_m | Water level in metres |
| rainfall_mm | Rainfall amount |
| river_level_m | Downstream river level |
| data_quality | Quality-control status |

## Derived Variables

| Field | Description |
|---|---|
| rainfall_3hr_mm | 3-hour cumulative rainfall |
| rainfall_6hr_mm | 6-hour cumulative rainfall |
| lake_rate_m_hr | Lake-level rate of change |
| river_rate_m_hr | River-level rate of change |
| alert_level | Prototype alert classification |