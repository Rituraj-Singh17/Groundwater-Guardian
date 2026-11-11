# Groundwater Guardian - Data Dictionary

## 1. Dataset Information

- Dataset: Maharashtra Groundwater Telemetry
- Source agency: Central Ground Water Board (CGWB)
- File: maha.csv
- Format: CSV
- Observation period: 14 January 2023 to 31 December 2025
- Total records: 454,929
- Total columns: 21
- State: Maharashtra

## 2. Dataset Columns

| Column | Meaning | Data type |
|---|---|---|
| SlNo | Serial number | Integer |
| Station | Monitoring station name | String |
| Agency | Data collection agency | String |
| State LGD Code | State location code | Integer |
| State | State name | String |
| District LGD Code | District location code | Integer |
| District | District name | String |
| Tehsil | Tehsil metadata | String |
| Block | Block metadata | String |
| Village | Village metadata | String |
| River | River metadata | String |
| Basin | Basin metadata | String |
| Tributary | Tributary metadata | String |
| Subtributary | Subtributary metadata | String |
| SubSubtributary | Sub-subtributary metadata | String |
| Local River | Local river metadata | String |
| Latitude | Station latitude | Float |
| Longitude | Station longitude | Float |
| RL_MSL | Elevation/reference field as named in source | Float |
| Data Acquisition Time | Observation timestamp | DateTime |
| Groundwater Level Telemetry 6 Hourly (meter) | Groundwater-level measurement | Float |

## 3. Dataset Profile

- Total observations: 454,929
- Total columns: 21
- Unique station names: 178
- Unique station-location combinations: 179
- Invalid timestamps found: 0
- Exact duplicate rows: 0
- Duplicate station-time groups using the composite key: 0
- Date range: 2023-01-14 to 2025-12-31
- Most common consecutive sampling interval: 6 hours

## 4. Station Identification

Station names alone are not unique.

Example: Khandala_2 appears in both Nagpur and Aurangabad.

Provisional station identity:
Station + District + Latitude + Longitude.

This composite key must be reviewed against any official station identifier available in the source.

## 5. Missing and Unavailable Metadata

The source uses the dash character (-) for unavailable metadata.

Examples:
- Tehsil: 444,465 dash placeholders
- Block: 454,817 dash placeholders
- Village: 454,817 dash placeholders
- River and several related fields: 454,929 dash placeholders

These placeholders must not be confused with missing groundwater measurements.

## 6. Data Quality Findings

### Sampling intervals
Most consecutive observations are six hours apart.
Other intervals also occur and require gap investigation.

### Duplicate observations
The initial station-name-only check identified 1,981 groups.
After including District, Latitude and Longitude in station identity,
the corrected check identified zero duplicate station-time groups.

### Suspicious measurements
Two measurements exceed an absolute value of 1,000 metres:
- Asage: 7184.310 m on 2023-12-18 06:00
- Bhendala: 4272.907 m on 2025-09-18 12:00

These are flagged for investigation, not automatically deleted.

The lowest observed value was -198.410 m.
Its meaning and validity require verification against the source measurement convention.

## 7. Important Assumptions and Limitations

- The six-hour interval is a provisional expected sampling interval.
- Longer intervals may indicate missing observations, reporting delays,
  or other source-data limitations.
- Negative and extreme readings must not be automatically classified as faults.
- RL_MSL interpretation and the measurement reference convention need source verification.
- Missing metadata does not necessarily mean a faulty monitoring station.
- An anomaly indicates a suspicious observation, not confirmed equipment failure.
- Original source data must remain unchanged.

## 8. Next Steps

1. Build a reusable CSV ingestion pipeline.
2. Validate required columns and data types.
3. Parse timestamps and numeric measurements.
4. Normalize unavailable metadata without modifying the raw source.
5. Identify station-location combinations.
6. Generate validation reports.
7. Prepare the validated dataset for anomaly detection.
