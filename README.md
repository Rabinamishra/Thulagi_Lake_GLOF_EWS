# Thulagi Lake GLOF Early-Warning Decision-Support Prototype

A Python- and GIS-based research prototype for multi-indicator monitoring and
decision support for potential Glacial Lake Outburst Flood (GLOF) conditions
at Thulagi Lake, Nepal.

The prototype integrates satellite-derived lake-area observations, rainfall
time-series analysis, water-level telemetry, downstream hydrological analysis,
and exposure screening into a single decision-support workflow.

> **Status: Research and decision-support prototype**
>
> This project is not an operational GLOF warning system. The alert
> classifications are demonstrative and require further validation,
> calibration, real-time sensor infrastructure, hydrodynamic modelling,
> historical event validation, reliability testing, and institutional
> authorization before operational use.

---

## Project Overview

Glacial Lake Outburst Floods are high-impact hazards in the Himalayan region.
Effective early-warning systems require the integration of multiple
environmental indicators rather than relying on a single observation.

This project explores a prototype workflow for **Thulagi Lake, Nepal** that
combines:

- Sentinel-2 satellite observations
- MNDWI-based lake-water extraction
- Multi-year lake-area analysis
- Historical rainfall analysis
- Water-level telemetry
- Automatic water-level rate and trend calculation
- Water-level acceleration analysis
- DEM-based downstream drainage tracing
- Potential impact-corridor analysis
- OpenStreetMap-based exposure screening
- Multi-indicator alert logic
- Python-based decision-support interfaces

The overall objective is to demonstrate how geospatial analysis, remote
sensing, time-series analysis, and Python programming can be combined into a
prototype GLOF monitoring workflow.

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
                           ├──────────────────┐
                           │                  │
                           ▼                  ▼
                    RAINFALL DATA      WATER-LEVEL DATA
                           │                  │
                           ▼                  ▼
                   Rainfall Indicators   Rate / Trend
                           │              Acceleration
                           │                  │
                           └─────────┬────────┘
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
                    ┌────────────────┴───────────────┐
                    ▼                                ▼
             Desktop Interface                 Streamlit
               (Tkinter)                       Dashboard


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
Key Technical Components
1. Sentinel-2 Lake Monitoring

Sentinel-2 imagery was processed to extract the Thulagi Lake water surface
using the Modified Normalized Difference Water Index (MNDWI).

Multiple thresholds were tested during the workflow, with:

MNDWI ≥ 0.30

selected for the prototype lake-water extraction.

The processed Sentinel-2 raster uses:

Coordinate Reference System:
WGS 84 / UTM Zone 45N (EPSG:32645)


Spatial resolution:
10 m

The current locked lake-area time series contains six satellite observations:

Year	Water Pixels	Lake Area (km²)
2016	8,270	0.8270
2018	8,627	0.8627
2020	8,844	0.8844
2022	9,209	0.9209
2024	9,167	0.9167
2025	9,291	0.9291

These observations are used as satellite-derived environmental evidence in
the prototype rather than as standalone operational warning thresholds.

2. Rainfall Time-Series Analysis

The rainfall workflow contains 9,355 daily observations covering the
period from 2001 through 2026.

The analysis derives rainfall indicators including:

Daily rainfall
3-day accumulated rainfall
7-day accumulated rainfall
Historical 7-day rainfall percentile

The percentile-based approach provides a way to compare recent rainfall
conditions against the historical rainfall distribution.

Example prototype indicators include:

Daily rainfall
3-day accumulation
7-day accumulation
Historical 7-day percentile

These indicators are subsequently incorporated into the multi-indicator
decision logic.

3. Water-Level Telemetry

The prototype includes a timestamped water-level telemetry workflow.

Instead of requiring users to manually calculate derived variables, the
application derives them automatically from sequential observations.

The system calculates:

Current water level
Rate of water-level change
Rising / falling / stable trend
Water-level acceleration
Equivalent short-period change

Conceptually:

Timestamped Water Levels
          │
          ▼
      Δ Water Level
          │
          ▼
      Rate of Change
          │
          ▼
         Trend
          │
          ▼
      Acceleration

The current demonstration uses simulated water-level telemetry. The interface
is designed so that the same processing logic can later accept real sensor
observations.

4. Multi-Indicator Alert Engine

The prototype contains a Python alert engine that combines environmental
evidence from multiple sources.

Current evidence categories include:

Rainfall
Lake-area change
Water-level behaviour

The prototype produces three decision-support states:

NORMAL
WATCH
ALERT

The purpose of this logic is to demonstrate the architecture of a
multi-indicator early-warning workflow.

The thresholds are prototype thresholds and have not been validated as
official GLOF warning thresholds.

5. DEM and Downstream Hydrological Analysis

A processed DEM was used to investigate the potential downstream drainage
pathway from Thulagi Lake.

The workflow includes:

DEM preprocessing
D8 flow-direction analysis
Lake pour-point identification
Downstream flow-path tracing
Drainage-cell analysis
Potential impact-corridor generation

The current downstream tracing produced a pathway of approximately:

14.16 km

from the lake outlet/pour-point area.

The potential impact-corridor workflow identified approximately:

29,869 drainage cells
0.662 km² corridor area

These results provide spatial context for future inundation and exposure
modelling.

The downstream corridor is a spatial screening product and should not be
interpreted as a predicted GLOF inundation boundary.

6. Exposure Screening

OpenStreetMap-derived spatial data were used to investigate potential
downstream exposure.

The workflow considers features such as:

Buildings
Roads
Settlements
Points of interest
Other mapped infrastructure

A 1-km screening area around the monitoring area was also evaluated.

The exposure workflow is intended to provide contextual information for
future risk visualization and does not represent a validated flood-impact
prediction.

7. Decision-Support Interfaces

The project contains two interface approaches.

Desktop Application

The main desktop interface is implemented using:

Python
Tkinter
Matplotlib

It provides:

Rainfall input
Satellite lake-area input
Timestamped water-level input
Automatic telemetry calculations
Alert assessment
Water-level trend visualization
Decision-support output
Report-export functionality

The main application is:

app.py

and uses the alert engine located at:

scripts/alert_engine.py
Streamlit Dashboard

A separate Streamlit dashboard provides a browser-based visualization of the
prototype monitoring workflow.

It combines:

Rainfall indicators
Water-level indicators
Satellite-derived lake-area history
Prototype alert classification
Monitoring-area visualization

The dashboard is located at:

scripts/dashboard.py

It can be launched with:

streamlit run scripts/dashboard.py
Project Results and Current Prototype State

The current prototype brings together several independently processed
components into one workflow:

Component	Current Status
Sentinel-2 lake extraction	Completed
MNDWI threshold testing	Completed
Lake-area time series	Completed
Historical rainfall processing	Completed
Rainfall indicators	Completed
Water-level telemetry workflow	Prototype
Automatic rate/trend calculation	Implemented
Water-level acceleration	Implemented
D8 downstream tracing	Completed
Potential impact corridor	Completed
OSM exposure screening	Completed
Multi-indicator alert engine	Implemented
Desktop decision-support UI	Implemented
Streamlit dashboard	Implemented
Operational warning system	Not implemented
Repository Structure
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
Technology Stack
Programming and Data Analysis
Python
Pandas
NumPy
GeoPandas
Matplotlib
Application Development
Tkinter
Streamlit
Plotly
Remote Sensing
Sentinel-2
MNDWI
Raster-based water extraction
Multi-temporal satellite analysis
GIS and Spatial Analysis
ArcGIS Pro
SRTM DEM
D8 flow-direction analysis
Downstream drainage tracing
Spatial buffering
Exposure screening
OpenStreetMap data
Version Control
Git
GitHub
Running the Project
1. Clone the repository
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd GLOF-EWS
2. Create a virtual environment
python -m venv .venv
Windows
.venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Run the desktop application
python app.py
5. Run the Streamlit dashboard
streamlit run scripts/dashboard.py
Reproducibility and Data

Large raw and generated datasets are intentionally excluded from the Git
repository through .gitignore.

The repository therefore focuses on:

Processing scripts
Analysis workflows
Configuration
Documentation
Application code
GIS project structure

The data_dictionary.md file documents the project's data structure and
variables.

Limitations

This project is a research and technical prototype rather than an operational
early-warning system.

Key limitations include:

Water-level telemetry is currently simulated for demonstration.
Alert thresholds have not been operationally validated.
Satellite observations are periodic rather than continuous.
The lake-area series contains discrete observations rather than real-time
measurements.
No validated hydrodynamic inundation model is currently integrated.
The downstream corridor is not a predicted flood boundary.
Exposure screening does not provide flood depth, velocity, or damage
estimates.
Historical GLOF events have not been used to formally calibrate the alert
thresholds.
Operational deployment would require validated sensors, communications,
maintenance, institutional ownership, emergency protocols, and field
validation.
Future Development

Planned extensions include:

Real-time water-level telemetry ingestion
Automated rainfall data ingestion
Improved threshold calibration and validation
Hydrodynamic inundation modelling
Potentially affected-area visualization
Infrastructure and exposure visualization
Automated report generation
Interactive monitoring maps
Uncertainty assessment
Historical event-based validation
Improved operational-readiness assessment
Research Relevance

This project demonstrates the integration of several areas relevant to
geospatial science, environmental modelling, and natural-hazard research:

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

The project provides a practical example of applying geospatial and
computational methods to a Himalayan natural-hazard problem.

Author

Rabina Mishra

MSc Geology | GIS & Remote Sensing | Natural Hazard Applications

This project was developed as an independent research and technical
prototype exploring the integration of remote sensing, GIS, environmental
time-series analysis, hydrological reasoning, and Python-based
decision-support methods for GLOF risk monitoring.

Disclaimer

This repository presents a research prototype for demonstrating a
multi-indicator GLOF monitoring and decision-support workflow.

The NORMAL, WATCH, and ALERT classifications generated by the prototype are
not official warnings and must not be used for emergency decision-making.

Operational deployment would require scientific validation, field
instrumentation, hydrodynamic modelling, historical-event validation,
uncertainty assessment, institutional authorization, and integration with
an appropriate warning and emergency-response framework.