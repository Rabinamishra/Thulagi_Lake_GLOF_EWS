\# Thulagi Lake GLOF Early-Warning Decision-Support Prototype



A research-oriented prototype for multi-indicator monitoring of potential

Glacial Lake Outburst Flood (GLOF) conditions at Thulagi Lake, Nepal.



The system combines satellite-derived lake-area observations, rainfall

indicators, and water-level telemetry into a prototype decision-support

workflow that produces NORMAL, WATCH, or ALERT classifications.



> \*\*Project status: Research and decision-support prototype\*\*

>

> This is not an operational GLOF warning system. Operational deployment

> would require validated thresholds, real-time sensor infrastructure,

> hydrodynamic modelling, historical event validation, reliability testing,

> and institutional authorization.



\---



\## Project Overview



Glacial Lake Outburst Floods are a significant hazard in high-mountain

environments. Early-warning systems can combine multiple environmental

indicators to support situational awareness and risk assessment.



This project develops a prototype workflow for Thulagi Lake that integrates:



\- Sentinel-2 satellite observations

\- MNDWI-based lake-water extraction

\- Multi-year lake-area analysis

\- Historical rainfall analysis

\- Water-level telemetry

\- Water-level rate, trend, and acceleration calculations

\- Downstream drainage analysis

\- Potential exposure screening

\- Multi-indicator alert classification

\- A graphical decision-support interface



\---



\## System Workflow



```text

Sentinel-2 Imagery

&#x20;       │

&#x20;       ▼

MNDWI Water Extraction

&#x20;       │

&#x20;       ▼

Lake-Area Time Series

&#x20;       │

&#x20;       ├─────────────────────┐

&#x20;       │                     │

&#x20;       ▼                     ▼

Rainfall Analysis      Water-Level Telemetry

&#x20;       │                     │

&#x20;       ▼                     ▼

Rainfall Indicators    Rate / Trend / Acceleration

&#x20;       │                     │

&#x20;       └──────────┬──────────┘

&#x20;                  ▼

&#x20;         Multi-Indicator

&#x20;          Alert Engine

&#x20;                  │

&#x20;                  ▼

&#x20;       NORMAL / WATCH / ALERT

&#x20;                  │

&#x20;                  ▼

&#x20;      Decision-Support Interface

