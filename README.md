
# Thulagi Lake GLOF Early-Warning Decision-Support Prototype

A Python- and GIS-based research prototype for multi-indicator monitoring and
decision support for potential Glacial Lake Outburst Flood (GLOF) conditions
at Thulagi Lake, Nepal.

The prototype integrates satellite-derived lake-area observations, historical
rainfall analysis, timestamped water-level telemetry, downstream hydrological
analysis, and exposure screening into a single decision-support workflow.

> **Status: Research and decision-support prototype**
>
> This project is not an operational GLOF warning system. The NORMAL, WATCH,
> and ALERT classifications are prototype decision-support outputs and require
> further scientific validation, calibration, real-time sensor infrastructure,
> hydrodynamic modelling, historical-event validation, reliability testing,
> and institutional authorization before operational use.

---

# Project Overview

Glacial Lake Outburst Floods are high-impact hazards in the Himalayan region.
A robust early-warning framework should consider multiple environmental
indicators rather than relying on a single observation.

This project develops a prototype workflow for **Thulagi Lake, Nepal** that
combines:

- Sentinel-2 satellite observations
- MNDWI-based lake-water extraction
- Multi-year lake-area analysis
- Historical rainfall analysis
- Timestamped water-level telemetry
- Automatic water-level rate calculation
- Automatic water-level trend classification
- Water-level acceleration analysis
- DEM-based downstream drainage tracing
- Potential impact-corridor analysis
- OpenStreetMap-based exposure screening
- Multi-indicator prototype alert logic
- Python-based decision-support interfaces

The overall objective is to demonstrate how remote sensing, GIS,
time-series analysis, hydrological reasoning, and Python programming can be
combined into a reproducible GLOF monitoring and decision-support workflow.

---

# System Architecture

```text
                    SATELLITE MONITORING
                           │
                           ▼
                  Sentinel-2 Imagery
                           │
                           ▼
                     MNDWI Analysis
                           │
                           ▼
                 Lake-Water Extraction
                           │
                           ▼
                   Lake-Area Time Series
                           │
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       RAINFALL DATA              WATER-LEVEL DATA
             │                           │
             ▼                           ▼
   Daily / 3-day / 7-day         Timestamped Levels
   rainfall indicators                  │
             │                           ▼
             │                    Current Water Level
             │                           │
             │                           ▼
             │                    Rate of Change
             │                           │
             │                           ▼
             │                         Trend
             │                           │
             │                           ▼
             │                     Acceleration
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    MULTI-INDICATOR
                      ALERT ENGINE
                           │
                           ▼
                   NORMAL / WATCH / ALERT
                           │
                           ▼
                  DECISION-SUPPORT UI
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       Desktop Interface          Streamlit Dashboard
            Tkinter


                    SPATIAL HAZARD CONTEXT
                              │
                              ▼
                         DEM Analysis
                              │
                              ▼
                    D8 Flow / Drainage Path
                              │
                              ▼
                  Potential Impact Corridor
                              │
                              ▼
                    Exposure Screening
````

---

# Key Technical Components

## 1. Sentinel-2 Lake Monitoring

Sentinel-2 imagery was processed to extract the Thulagi Lake water surface
using the Modified Normalized Difference Water Index (MNDWI).

Multiple MNDWI thresholds were tested during the workflow.

The selected prototype threshold is:

**MNDWI ≥ 0.30**

The processed Sentinel-2 raster uses:

* **Coordinate Reference System:** WGS 84 / UTM Zone 45N
* **EPSG:** 32645
* **Spatial resolution:** 10 m

## Locked Lake-Area Dataset

The current prototype uses the following verified satellite-derived
lake-area observations:

| Year | Water Pixels | Lake Area (km²) |
| ---- | -----------: | --------------: |
| 2016 |        8,270 |          0.8270 |
| 2018 |        8,627 |          0.8627 |
| 2020 |        8,844 |          0.8844 |
| 2022 |        9,209 |          0.9209 |
| 2024 |        9,167 |          0.9167 |
| 2025 |        9,291 |          0.9291 |

These observations provide long-term satellite-derived environmental
evidence for the prototype decision-support workflow.

The satellite observations are periodic rather than continuous and are
therefore not treated as real-time warning observations.

---

# 2. Rainfall Time-Series Analysis

The rainfall workflow contains **9,355 daily observations** covering the
period from 2001 through 2026.

The system derives rainfall indicators including:

* Daily rainfall
* 3-day accumulated rainfall
* 7-day accumulated rainfall
* Historical 7-day rainfall percentile

The percentile-based approach compares recent rainfall conditions with the
historical rainfall distribution.

The rainfall indicators are provided to the prototype alert engine as one
source of environmental evidence.

## Example Current Rainfall Indicators

The current processed dataset provides:

| Indicator                   |              Value |
| --------------------------- | -----------------: |
| Daily rainfall              |           10.47 mm |
| 3-day rainfall              |           46.50 mm |
| 7-day rainfall              |          132.45 mm |
| Historical 7-day percentile | 98.08th percentile |

The rainfall percentile is used to characterize whether recent rainfall
conditions are relatively elevated compared with the historical record.

---

# 3. Water-Level Telemetry

Water level is a **direct decision-making input** in the prototype.

The system is designed around timestamped water-level observations rather than
requiring the user to manually enter rate, trend, or acceleration values.

The workflow is:

```text
Timestamped Water-Level Observations
                  │
                  ▼
          Current Water Level
                  │
                  ▼
          Δ Water Level / Δ Time
                  │
                  ▼
        Rate of Water-Level Change
                  │
                  ▼
          Rising / Falling / Stable
                  │
                  ▼
       Change in Rate / Acceleration
                  │
                  ▼
        Water-Level Evidence
                  │
                  ▼
          Prototype Alert Engine
```

## Water-Level Variables Used in Decision Making

The water-level component provides the decision engine with:

1. **Current water level**
2. **Recent water-level change**
3. **Rate of water-level change**
4. **Water-level trend**
5. **Water-level acceleration**

These values are calculated automatically from sequential timestamped
observations.

The user therefore provides the **observed water level and timestamp** rather
than manually calculating derived hydrological indicators.

## Current Demonstration Dataset

The present prototype demonstration uses simulated water-level telemetry
while preserving the same processing structure required for future real
sensor observations.

The demonstration series contains:

* **145 timestamped observations**
* Starting water level: **22.41 m**
* Latest water level: **23.05 m**
* Latest rise rate: approximately **0.034 m/hour**

The simulated dataset is used to test the telemetry-processing and
decision-making workflow.

It is not presented as actual measured Thulagi Lake sensor data.

## Role in Decision Making

Water level is not merely displayed for visualization.

It contributes directly to the prototype's multi-indicator evidence
assessment alongside rainfall and lake-area information.

The decision pathway is:

```text
Observed Water Level
        │
        ├── Current Level
        ├── Rate
        ├── Trend
        └── Acceleration
                 │
                 ▼
        Water-Level Evidence
                 │
                 ▼
          Alert Engine
```

This makes the water-level telemetry component one of the core
decision-making inputs of the prototype.

---

# 4. Multi-Indicator Alert Engine

The prototype contains a Python-based alert engine that combines evidence
from multiple environmental indicators.

The current decision-making evidence categories are:

* **Rainfall**
* **Water-level behaviour**
* **Lake-area change**

The engine produces three prototype decision-support states:

```text
NORMAL
WATCH
ALERT
```

The purpose of the engine is to demonstrate how independent environmental
signals can be combined into a transparent decision-support framework.

The prototype does not treat any single indicator as sufficient by itself.

## Decision-Making Structure

```text
             RAINFALL
                 │
                 │
                 ▼
        Rainfall Evidence
                 │
                 │
WATER LEVEL ─────┼───── LAKE AREA
     │           │          │
     ▼           │          ▼
Level / Rate     │     Area Change
Trend / Accel.   │
     │           │
     └───────────┴──────────┘
                 │
                 ▼
          Combined Evidence
                 │
                 ▼
           Evidence Score
                 │
                 ▼
       Prototype Alert Level
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     NORMAL    WATCH     ALERT
```

The alert engine records the evidence contributing to the resulting
classification so that the output remains interpretable.

## Prototype Alert Scoring

Rainfall evidence is evaluated using the rainfall indicators and historical
percentile.

Water-level evidence is derived from the observed telemetry behaviour.

Lake-area evidence is derived from the satellite lake-area time series.

The resulting evidence is combined into a prototype score that determines
the displayed decision-support state.

The thresholds and scoring rules are **prototype thresholds**.

They are not official GLOF warning thresholds and have not been validated
for operational emergency warning.

---

# 5. DEM and Downstream Hydrological Analysis

A processed DEM was used to investigate the potential downstream drainage
pathway from Thulagi Lake.

The workflow includes:

* DEM preprocessing
* D8 flow-direction analysis
* Lake pour-point identification
* Downstream flow-path tracing
* Drainage-cell analysis
* Potential impact-corridor generation

The current processed Thulagi DEM has:

* **Resolution:** approximately 28.895 m
* **Raster size:** 757 × 782 cells
* **Minimum elevation:** approximately 656 m
* **Maximum elevation:** approximately 7,979 m

The downstream D8 trace begins from the identified lake outlet/pour-point
area.

The resulting downstream pathway is approximately:

**14.16 km**

The potential impact-corridor workflow identified approximately:

* **29,869 drainage cells**
* **0.662 km² corridor area**

These outputs provide spatial context for downstream hazard and exposure
analysis.

The corridor is a **drainage-based spatial screening product**.

It should not be interpreted as a predicted GLOF inundation boundary.

---

# 6. Exposure Screening

OpenStreetMap-derived spatial data were used to investigate potential
downstream exposure.

The workflow considers features including:

* Buildings
* Roads
* Settlements
* Points of interest
* Other mapped infrastructure

A 1-km screening area around the monitoring area was also evaluated.

The exposure workflow provides spatial context for risk visualization and
future inundation analysis.

It does not currently estimate:

* Flood depth
* Flow velocity
* Structural damage
* Economic loss
* Probabilistic risk

---

# 7. Decision-Support Interfaces

The project contains two interface approaches.

## Desktop Application

The main desktop interface is implemented using:

* Python
* Tkinter
* Matplotlib

The desktop application provides:

* Rainfall indicators
* Satellite lake-area information
* Timestamped water-level input
* Automatic telemetry calculations
* Water-level trend visualization
* Multi-indicator alert assessment
* Decision-support output
* Report/export functionality

The main application is:

```text
app.py
```

The alert engine is located at:

```text
scripts/alert_engine.py
```

## Streamlit Dashboard

A separate Streamlit dashboard provides a browser-based visualization of the
prototype monitoring workflow.

It combines:

* Rainfall indicators
* Water-level indicators
* Satellite-derived lake-area history
* Prototype alert classification
* Monitoring-area visualization

The dashboard is located at:

```text
scripts/dashboard.py
```

Run it using:

```bash
streamlit run scripts/dashboard.py
```

---

# Project Results and Current Prototype State

| Component                              | Status                 |
| -------------------------------------- | ---------------------- |
| Sentinel-2 lake extraction             | Completed              |
| MNDWI threshold testing                | Completed              |
| MNDWI threshold selection              | Completed              |
| Locked lake-area time series           | Completed              |
| Historical rainfall processing         | Completed              |
| Rainfall indicators                    | Completed              |
| Water-level telemetry workflow         | Implemented and tested |
| Automatic water-level rate calculation | Implemented and tested |
| Automatic trend calculation            | Implemented and tested |
| Water-level acceleration               | Implemented and tested |
| Water-level decision input             | Implemented and tested |
| D8 downstream tracing                  | Completed              |
| Potential impact corridor              | Completed              |
| OSM exposure screening                 | Completed              |
| Multi-indicator alert engine           | Implemented and tested |
| NORMAL / WATCH / ALERT classification  | Implemented and tested |
| Desktop decision-support UI            | Implemented and tested |
| Streamlit dashboard                    | Implemented            |
| Operational warning system             | Not implemented        |

---

# Repository Structure

```text
GLOF-EWS/
│
├── app.py
│   └── Main desktop decision-support interface
│
├── EWS.py
│   └── Additional prototype interface/workflow
│
├── scripts/
│   ├── alert_engine.py
│   ├── analyze_lake_timeseries.py
│   ├── analyze_mndwi.py
│   ├── analyze_rainfall.py
│   ├── analyze_water_level.py
│   ├── apply_s2_mask.py
│   ├── calculate_lake_areas.py
│   ├── clip_hydro_dem.py
│   ├── create_impact_corridor.py
│   ├── download_rainfall.py
│   ├── download_s2.py
│   ├── extract_exposure.py
│   ├── extract_osm_exposure.py
│   ├── extract_s2.py
│   ├── process_s2_indices.py
│   ├── simulate_water_level.py
│   ├── trace_downstream.py
│   ├── trace_downstream_extended.py
│   └── validate_s2_products.py
│
├── src/
│   ├── alert_engine.py
│   ├── generate_sensor_data.py
│   ├── imerg_ingest.py
│   └── rainfall_processing.py
│
├── config/
│   └── thresholds.csv
│
├── GLOF_EWS/
│   ├── GLOF_EWS.aprx
│   ├── GLOF_EWS.atbx
│   └── thulagi_downstream.kml
│
├── data_dictionary.md
├── project_scenario.md
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Technology Stack

## Programming and Data Analysis

* Python
* Pandas
* NumPy
* GeoPandas
* Matplotlib

## Application Development

* Tkinter
* Streamlit
* Plotly

## Remote Sensing

* Sentinel-2
* MNDWI
* Raster-based water extraction
* Multi-temporal satellite analysis

## GIS and Spatial Analysis

* ArcGIS Pro
* DEM analysis
* D8 flow-direction analysis
* Downstream drainage tracing
* Spatial buffering
* Exposure screening
* OpenStreetMap data

## Version Control

* Git
* GitHub

---

# Running the Project

## 1. Clone the Repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd GLOF-EWS
```

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the Desktop Application

```bash
python app.py
```

## 5. Run the Streamlit Dashboard

```bash
streamlit run scripts/dashboard.py
```

---

# Reproducibility and Data

Large raw and generated datasets are intentionally excluded from the Git
repository through `.gitignore`.

The repository therefore focuses on:

* Processing scripts
* Analysis workflows
* Configuration
* Documentation
* Application code
* GIS project structure

The `data_dictionary.md` file documents the project's data structure and
variables.

The prototype is designed so that simulated water-level observations can
eventually be replaced by real timestamped sensor observations without
changing the overall decision-support architecture.

---

# Limitations

This project is a research and technical prototype rather than an
operational early-warning system.

Key limitations include:

* Water-level telemetry is currently simulated for demonstration.
* Real-time sensor hardware and communications are not yet integrated.
* Alert thresholds have not been operationally validated.
* Satellite observations are periodic rather than continuous.
* The lake-area series contains discrete satellite observations.
* No validated hydrodynamic inundation model is currently integrated.
* The downstream corridor is not a predicted flood boundary.
* Exposure screening does not provide flood depth, velocity, or damage
  estimates.
* Historical GLOF events have not been used to formally calibrate the alert
  thresholds.
* The prototype does not replace official monitoring or emergency-warning
  systems.

Operational deployment would require:

* Validated water-level sensors
* Reliable telemetry and communications
* Field installation and maintenance
* Scientific threshold calibration
* Historical-event validation
* Hydrodynamic inundation modelling
* Uncertainty assessment
* Reliability and failure-mode testing
* Institutional ownership
* Emergency protocols
* Field validation
* Integration with an appropriate warning and emergency-response framework

---

# Future Development

Potential future extensions include:

* Real-time water-level telemetry ingestion
* Automated rainfall data ingestion
* Field sensor integration
* Improved threshold calibration and validation
* Hydrodynamic inundation modelling
* Potentially affected-area visualization
* Infrastructure and exposure visualization
* Automated report generation
* Interactive monitoring maps
* Uncertainty assessment
* Historical event-based validation
* Sensor quality-control procedures
* Communication-failure handling
* Operational-readiness assessment

---

# Research Relevance

This project demonstrates the integration of:

```text
Remote Sensing
      +
GIS
      +
Hydrological Analysis
      +
Time-Series Analysis
      +
Python Programming
      +
Decision-Support Systems
      =
GLOF Monitoring Prototype
```

The project provides a practical example of applying geospatial and
computational methods to a Himalayan natural-hazard problem.

The key contribution of the prototype is the integration of multiple
environmental evidence sources into a transparent decision-support workflow.

In particular, the water-level component demonstrates how raw timestamped
telemetry can be transformed automatically into rate, trend, and acceleration
indicators and subsequently incorporated into multi-indicator decision
making.

The prototype therefore connects:

```text
OBSERVATION
     │
     ▼
PROCESSING
     │
     ▼
INDICATOR GENERATION
     │
     ▼
EVIDENCE ASSESSMENT
     │
     ▼
DECISION SUPPORT
```

This structure provides a foundation for future research involving real-time
sensor data, hydrodynamic modelling, uncertainty analysis, and operational
early-warning development.

---

# Author

**Rabina Mishra**

**MSc Geology | GIS & Remote Sensing | Natural Hazard Applications**

This project was developed as an independent research and technical
prototype exploring the integration of remote sensing, GIS, environmental
time-series analysis, hydrological reasoning, and Python-based
decision-support methods for GLOF risk monitoring.

---

# Disclaimer

This repository presents a research prototype for demonstrating a
multi-indicator GLOF monitoring and decision-support workflow.

The **NORMAL, WATCH, and ALERT** classifications generated by the prototype
are decision-support outputs and are **not official warnings**.

The prototype must not be used as a substitute for official emergency
warning systems or emergency decision-making.

Operational deployment would require scientific validation, field
instrumentation, hydrodynamic modelling, historical-event validation,
uncertainty assessment, reliability testing, institutional authorization,
and integration with an appropriate warning and emergency-response
framework.

