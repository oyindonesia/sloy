# sloy

sloy is a tool to collect and export SLO (Service Level Objectives) metrics, inspired by [Google's slo-generator](https://github.com/google/slo-generator). The main use case of sloy is to collect data and determine the first initial SLO.

## Features
Backends:
- Elasticsearch
- Google Cloud Logging

Exporters:
- Google Sheets
- Slack

## Getting Started
### Prerequisites
Make sure you have [rye](https://rye.astral.sh/) installed for Python package management.
### Installation
```bash
git clone https://github.com/oyindonesia/sloy.git
cd sloy

# Install dependencies
rye sync
```
### Development
To run the app in development mode:
```
rye run dev
```
## Usage
### Global Configuration
Global configuration is used for storing backends and exporters shared configuration. Sample config:
```yaml
---
backends:
  elasticsearch:
    url: ${ELASTICSEARCH_URL}
    basic_auth:
      username: ${ELASTICSEARCH_USERNAME}
      password: ${ELASTICSEARCH_PASSWORD}
  cloudlogging:
    credentials: ${GCP_CREDENTIALS}
    project_id: ${GCP_PROJECT_ID}
exporters:
  slack:
    token: ${SLACK_TOKEN}
    channel: ${SLACK_CHANNEL}
  gsheets:
    credentials: ${GCP_CREDENTIALS}
    sheet_id: ${SHEET_ID}
    worksheet_name: Sheet1
```
For each backend, the required fields are:
- `elasticsearch`: Elasticsearch backend configuration
  - `url`: Elasticsearch URL
  - `basic_auth`: Basic authentication configuration
    - `username`: Elasticsearch username
    - `password`: Elasticsearch password
- `cloudlogging`: Google Cloud Logging backend configuration
    - `credentials`: Google Cloud credentials
    - `project_id`: Google Cloud project ID

For each exporter, the required fields are:
- `slack`: Slack exporter configuration
  - `token`: Slack token
  - `channel`: Slack channel
- `gsheets`: Google Sheets exporter configuration
    - `credentials`: Google Cloud credentials
    - `sheet_id`: Google Sheets ID
    - `worksheet_name`: Google Sheets worksheet name

### SLO Configuration
SLO configuration is used for defining SLOs. Sample config:
```yaml
name: Database Latency SLO
description: >
  Latency for Postgres Database, 99th percentile of latencies should be less than 10ms
backend: elasticsearch
exporters:
  - gsheets:
      sheet_id: THIS_IS_A_GOOGLE_SHEET_ID
      worksheet_name: database_latency
time_window: 7d
method: percentile
service_level_indicator:
  percentiles: [95.0, 99.0, 99.9]
  es_index: traces-apm*,apm-*,logs-apm*,apm-*,metrics-apm*,apm-*
  value_key: transaction.duration.us
  query: >
    {
      "query": {
        "bool": {
          "must": [],
          "filter": [
              {
                  "exists": {
                      "field": "transaction.duration.us"
                  }
              },
              {
                  "match_phrase": {
                      "labels.db_system": "postgresql"
                  }
              }
          ],
          "should": [],
          "must_not": []
        }
      }
    }
```
The required fields are:
- `name`: SLO name
- `backend`: Backend to use
- `method`: Method to calculate SLO, the available methods are:
  - `percentile`: Calculate SLO based on percentile
  - `error_rate`: Calculate SLO based on bad / all events
- `service_level_indicator`: Service level indicator configuration, this depends on the backend and the method used
- `time_window`: Time window to calculate SLO

The optional fields are:
- `description`: SLO description
- `exporters`: Exporters to use
