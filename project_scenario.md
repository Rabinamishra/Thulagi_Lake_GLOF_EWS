# Nepal GLOF-EWS-DIMS Prototype

## 1. Prototype Scenario

This project demonstrates a prototype Disaster Information Management
and Early Warning System (DIMS/EWS) for GLOF and downstream flood-risk
monitoring in Nepal's Hindu Kush Himalayan region.

The demonstration scenario is based on the Thulagi glacial lake
context in the Gandaki basin.

This is a technical demonstration prototype and does not represent
the operational monitoring system of the Government of Nepal or UNDP.

## 2. Hazard

Primary hazard:
Glacial Lake Outburst Flood (GLOF)

Secondary hazard:
Downstream river flooding

## 3. Monitoring Concept

The prototype combines:

- rainfall observations
- glacial-lake water-level observations
- downstream river-level observations
- sensor-health information
- geospatial hazard and exposure information

## 4. Prototype Monitoring Stations

### THU-LAKE-01
Purpose:
Monitor lake water level.

Variables:
- water level
- rate of water-level change
- sensor status
- battery status
- transmission status

### THU-RAIN-01
Purpose:
Monitor precipitation.

Variables:
- rainfall
- cumulative rainfall
- sensor status
- transmission status

### THU-RIVER-01
Purpose:
Monitor downstream river conditions.

Variables:
- river water level
- rate of water-level change
- sensor status
- transmission status

## 5. System Workflow

Sensor / Earth Observation Data
        ↓
Data Ingestion
        ↓
Data Quality Control
        ↓
Hydrological Analysis
        ↓
Alert Assessment
        ↓
GIS Impact Analysis
        ↓
Decision-Support Dashboard
        ↓
Warning Communication

## 6. Alert Levels

The prototype will use four demonstration alert levels:

- NORMAL
- WATCH
- ALERT
- WARNING

The thresholds used by this prototype are illustrative and are not
official operational warning thresholds for Thulagi or any other
glacial lake.

## 7. Decision-Support Outputs

The dashboard will display:

- current hazard status
- rainfall conditions
- lake water level
- downstream river level
- rate of change
- sensor/data quality
- monitoring station status
- potentially affected areas
- warning messages
- Nepali communication
- accessible communication formats

## 8. Data Sources

The prototype will distinguish clearly between:

1. Real/near-real-time Earth observation data
2. Simulated hydrometeorological sensor data
3. Geospatial datasets
4. Demonstration thresholds

No simulated data will be presented as official operational observations.

## 9. Intended Users

Primary users:

- disaster-risk analysts
- project management/technical teams
- hydrological and meteorological agencies
- local government/disaster-management personnel

The system is intended as a decision-support prototype rather than
an autonomous emergency-warning authority.