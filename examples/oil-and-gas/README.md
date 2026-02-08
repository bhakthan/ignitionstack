# Oil & Gas Example — PredictMaint System

This example demonstrates the IgnitionStack pattern for an **equipment maintenance prediction system**.

## Run It

```bash
ignition run examples/oil-and-gas/use-case.txt --project predictmaint
```

## What Gets Generated

- **Bicep infra** with IoT Hub, Event Hubs, Time Series Insights
- **Sensor data pipeline** for real-time telemetry ingestion
- **Predictive failure agent** with ML model scaffolding
- **Safety monitoring dashboard** with alert escalation
- **Edge computing** configuration (Azure IoT Edge)

## Domain-Specific Agents

| Agent | Role |
|-------|------|
| Safety Inspector | Validates safety protocols and compliance with API/OSHA standards |
| Anomaly Detector | Monitors sensor feeds for abnormal patterns |
| Maintenance Optimizer | Schedules preventive maintenance to minimize downtime |
