# Synthetic Demo: Smart-Bin Sensor Fault SOP

> This document is synthetic test data. It is not an official company policy and is not legally or operationally authoritative.

## Purpose

Provide a repeatable demonstration workflow for handling a smart-bin sensor that reports missing or implausible measurements without inventing telemetry.

## Scope

This demo applies to training records for smart-bin identifiers such as `BIN-DEMO-001`. It covers missing fill level, missing weight, low battery, and persistent communication faults.

## Procedure

1. Confirm the sensor status and record the timestamp, bin ID, battery level, and available measurements.
2. Preserve missing fill-level or weight values as missing; never replace them with zero.
3. Retry a remote health check once and record the result under incident code `SENSOR-DEMO-FAULT`.
4. If communication returns, monitor the next two readings before closing the demo incident.
5. If the fault persists, create a maintenance task and label the bin for manual inspection.

## Escalation rules

- Escalate immediately if temperature indicates a possible fire risk.
- Escalate after two consecutive failed health checks for any other sensor fault.
- Notify dispatch when collection decisions could be affected by missing data.

## Responsible department

Synthetic owner: Operations Technology Demo Team.

## Version

Demo version 1.0.

## Effective date

2026-01-01 (synthetic testing date only).
