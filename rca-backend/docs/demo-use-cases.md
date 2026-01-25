# RCA Platform - Demo Use Cases

Real use cases extracted from JIRA (Project MM) for demonstration purposes.

---

## Category 1: ETA/Tracking Issues

### Use Case 1.1: Missing ETA Investigation
**JIRA:** MM-13293 | **Priority:** High

**Scenario:** Milwaukee Tools shipments are missing FourKites ETAs.

**Sample Containers:**
- HAMU2868590
- UACU5717394
- TXGU7118400
- HLBU3242168

**Demo Prompt:**
```
Why are these containers missing FK ETA? HAMU2868590, UACU5717394
```

**Expected Agent Flow:**
1. Tracking API Agent → Check if containers exist, get current status
2. **DataHub SuperAPI Agent → Get all ocean events for these containers** ⭐
3. DWH Agent → Query tracking history, check if ETA was ever calculated
4. Coordinator → Correlate data, identify root cause (missing events = no ETA)

---

### Use Case 1.2: Incorrect ETA at Delivery
**JIRA:** MM-13255 | **Shipper:** Klein Tools

**Scenario:** Customer needs accurate ETAs from departure for air vs. ocean freight decisions. Static/stuck ETAs causing business impact.

**Demo Prompt:**
```
Klein Tools shipment has static ETA that's not updating. Container XXXX. Why is the ETA stuck?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get current tracking status, last update time
2. **DataHub SuperAPI Agent → Get latest carrier events and timestamps** ⭐
3. DWH Agent → Check ETA calculation history, inference events
4. Coordinator → Determine if carrier data stopped or calculation issue

---

## Category 2: Carrier Data Issues

### Use Case 2.1: Incorrect Carrier Events
**JIRA:** MM-13313 | **Shipper:** Louis Dreyfus Company (LDC)

**Scenario:** Incorrect VA/VD (Vessel Arrival/Vessel Departure) events applied on load ONEYTAOFL2320900.

**Demo Prompt:**
```
Load ONEYTAOFL2320900 has incorrect VA/VD events. Can you investigate what happened?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get current events timeline
2. **DataHub SuperAPI Agent → Get all ocean events from carrier** ⭐
3. DWH Agent → Query event history, source of VA/VD events
4. Coordinator → Compare carrier events vs applied events, identify discrepancy

---

### Use Case 2.2: Incorrect Inferred Events
**JIRA:** MM-13242 | **Shipper:** P&G LATAM | **Carrier:** Evergreen

**Scenario:** Load 1418779680 has incorrect inferred VA event. Carrier website shows different date.

**Demo Prompt:**
```
P&G load 1418779680 has wrong inferred VA event. The carrier shows different arrival date. What went wrong?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get current tracking and inferred events
2. **DataHub SuperAPI Agent → Get actual carrier VA event timestamp** ⭐
3. DWH Agent → Check inference logic execution, data sources used
4. Coordinator → Compare carrier data vs inferred data, identify inference bug

---

### Use Case 2.3: Wrong POD Stop
**JIRA:** MM-13229 | **Shipper:** Schreiber Foods | **Carrier:** Evergreen

**Scenario:** Shipment 192060 shows POD as TWTPE but carrier shows TWKHH as POD and TWTPE as Place of Delivery.

**Demo Prompt:**
```
Shipment 192060 has wrong POD location. Shows TWTPE but should be TWKHH. Why is POD incorrect?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get shipment route and stops
2. **DataHub SuperAPI Agent → Get carrier routing from ocean events** ⭐
3. DWH Agent → Check routing data source, carrier parser logic
4. Coordinator → Compare carrier route vs FK route, determine parsing issue

---

## Category 3: Operational Issues

### Use Case 3.1: Stuck at POD
**JIRA:** MM-13309 | **Customer:** Tama

**Scenario:** Scheduled export shows blank "Stuck at POD" column.

**Demo Prompt:**
```
Why is the Stuck at POD column showing blank for customer Tama's scheduled report?
```

**Expected Agent Flow:**
1. DWH Agent → Query stuck_at_pod calculation logic
2. Athena Agent → Check if data exists in export tables
3. Coordinator → Identify sync or calculation issue

---

### Use Case 3.2: Kafka Lag Investigation
**JIRA:** MM-13300

**Scenario:** Production event validation Kafka topic had significant consumer lag between Jan 7-13.

**Demo Prompt:**
```
What caused the Kafka lag in prod_event_validation_request topic between Jan 7-13?
```

**Expected Agent Flow:**
1. Logs Agent → Check service logs for errors during that period
2. DWH Agent → Query event processing metrics
3. Coordinator → Correlate lag with specific events or deployments

---

### Use Case 3.3: Load Alerts Missing
**JIRA:** MM-13299 | **Shipper:** P&G

**Scenario:** Loads have "Booking container mismatch" and "Invalid booking numbers" but no load alerts generated.

**Load Numbers:** 1418744386, 1418698310, 1418619817

**Demo Prompt:**
```
P&G loads 1418744386, 1418698310 have booking mismatches but no alerts. Why are alerts not triggering?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get load details and validation status
2. DWH Agent → Check alert rules and execution history
3. Coordinator → Identify if alert rules missing or suppressed

---

## Category 4: Data Accuracy

### Use Case 4.1: Past Date on Delivery
**JIRA:** MM-13267 | **Shipper:** P&G LATAM | **Carrier:** Maersk

**Scenario:** Load 1418724159 created Nov 11, VA at POD on Jan 2, but delivery ATA shows past date.

**Demo Prompt:**
```
Load 1418724159 shows ATA in the past even though VA just happened on Jan 2. Why is the date incorrect?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get timeline of all events
2. DWH Agent → Query event processing order and timestamps
3. Coordinator → Identify timestamp handling issue

---

### Use Case 4.2: Operating Carrier Not Updating
**JIRA:** MM-13292 | **Shipper:** Coca-Cola CPS

**Scenario:** Auto identification enabled for CPS but operating carrier not being assigned correctly.

**Demo Prompt:**
```
Coca-Cola CPS shipments have auto identification enabled but operating carrier isn't updating. What's wrong?
```

**Expected Agent Flow:**
1. Tracking API Agent → Get shipment carrier assignments
2. DWH Agent → Check auto-identification rules and execution logs
3. Coordinator → Identify rule matching or execution issue

---

## Quick Demo Script

For a 10-minute demo, use these three prompts in sequence:

1. **Simple Query (2 min):**
   ```
   What's the current status of container HAMU2868590?
   ```

2. **Investigation (4 min):**
   ```
   Load 1418779680 has incorrect VA event. The carrier shows Dec 23 arrival but we sent wrong date. What happened?
   ```

3. **Multi-source Analysis (4 min):**
   ```
   P&G loads 1418744386 and 1418698310 have booking container mismatch but no alerts were generated. Can you investigate why?
   ```

---

## Data Sources Used

| Agent | Data Source | Query Type |
|-------|-------------|------------|
| Tracking API | REST API | Container/Shipment lookup |
| **DataHub SuperAPI** | **Ocean SuperAPI** | **All carrier events (VA, VD, GT, DL, etc.)** ⭐ |
| DWH Agent | Redshift | Historical data, metrics |
| Athena Agent | S3/Athena | Event logs, raw data |
| Logs Agent | SigNoz/ClickHouse | Service logs |

---

## Notes for Demo

1. **Use real container numbers** from the examples above for more realistic responses
2. **Start with simple queries** to show basic agent capabilities
3. **Progress to investigations** to show multi-agent coordination
4. **Highlight the SSE progress updates** during longer investigations
5. **Show the reasoning traces** to demonstrate transparency
