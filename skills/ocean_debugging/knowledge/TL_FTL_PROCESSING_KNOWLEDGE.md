# TL & FTL Processing Knowledge Base

*Source: Support Team SMEs - Sample Log Repository for Rewind Tool*

## Processing Flow Overview

### Three Main Processing Flows:

1. **CarrierLink Processing Flow** (Blue)
   - NEW_DRIVER_LOCATION AND "DriverPhone#" (global-worker)

2. **Files Processing Flow** (Red)
   - ProcessSuperFilesTask AND "LoadNumber" (Carrier Files Worker)
   - PROCESS_SUPER_RECORD AND "LoadNumber" (Carrier Files Worker)
   - API Processing Flow:
     - PROCESS_TRUCK_RECORD AND "LoadNumber" (Carrier Files Worker)
     - CARRIER_LOAD_UPDATE AND "LoadNumber" (Carrier Files Worker)
     - PROCESS_TRUCK_LOCATION AND "LoadNumber" (Global Worker Ex)
     - TL_STATUS_UPDATES AND "TrackingID" (Global Worker)

3. **GPS Processing Flow** (Green)
   - FETCH_ELD_LOCATION AND "LoadNumber" or "TrackingID" (cfw-eld-data)
   - PROCESS_ELD_LOCATION AND "LoadNumber" (global-worker-tracking)

### Final Common Steps:
- PROCESS_NEW_LOCATION AND "TrackingID" (Location Worker)
- POST_LOCATION_UPDATE AND "LoadNumber" or "TrackingID" (Integration Worker)

---

## Key Log Messages & Their Meanings

### LR-001: ProcessSuperFilesTask (Data Ingestion)
**Purpose**: Captures inbound Carrier file payload in raw state before processing

**Service**: `carrier-files-worker`

**Transmission Types**: EDI 214, Files

**Search Keywords**: Filename, Mapped Identifier, Permalink

**Shipment Modes**: Courier, FTL, LTL, TL

**Sample Log**:
```
[ProcessSuperFilesTask] PROCESS record: 1175,
file: FRS-MGRB-20251010140003.csv-24.csv,
carrier: mgrb,
Data: ["MARSSTMO", "870731120", "870731120", "141", "49253",
       "32.620335", "-96.807959", "32.572878", "-94.768032",
       "2023-11-21 17:05:00.0", "SO", "2023-11-21 19:00:00.0",
       "2023-11-21 19:00:00.0", "2", "75605"]
```

**What to Look For**:
- File name format issues
- Carrier permalink mismatch
- Data format errors
- Missing required fields

**Common Root Causes**:
- Malformed carrier file
- Incorrect file format
- Missing carrier configuration
- File parsing error

---

### LR-002: PROCESS_SUPER_RECORD (Data Mapping)
**Purpose**: File or API data mapped per configuration and enqueued for next stage

**Service**: `carrier-files-worker`

**Transmission Types**: DispatcherUpdateAPI, EDI 214, EDI 315, Files

**Search Keywords**: Mapped Identifier, Permalink

**Shipment Modes**: FTL, Intermodal, LTL, Ocean, Parcel, Rail, TL

**Sample Log**:
```json
{
  "MessageType": "PROCESS_SUPER_RECORD",
  "Source": "dispatcher_updates_api",
  "ApiRequestUuid": "9ae59302-3876-49f7-9639-78befb78d486",
  "Content": {
    "Carrier": "mcabee-trucking-inc",
    "Mode": "api",
    "TrackingMethod": "dispatcher_updates_api",
    "LoadIdentifier": "85592702",
    "Latitude": 35.2225969,
    "Longitude": -80.9702462,
    "LocatedAt": "2025-10-08T10:14:01.447Z"
  }
}
```

**What to Look For**:
- Missing LoadIdentifier
- Invalid carrier permalink
- Missing required mapping fields
- Incorrect tracking method

**Common Root Causes**:
- Mapping configuration missing
- Carrier configuration incorrect
- Missing identifier in source data
- Invalid data format

---

### LR-003: PROCESS_TRUCK_RECORD (Asset Assignment)
**Purpose**: Assigns tracking assets (Truck, Trailer, Driver Phone) and Operating SCAC

**Service**: `carrier-files-worker`

**Transmission Types**: DispatcherUpdateAPI, EDI 214, EDIFACT, Files

**Search Keywords**: Asset Number, Mapped Identifier, Permalink

**Shipment Modes**: FTL, TL

**Sample Log**:
```json
{
  "MessageType": "PROCESS_TRUCK_RECORD",
  "Source": "dispatcher_updates_api",
  "Content": {
    "Carrier": "amazoncom",
    "LoadIdentifier": "320845506",
    "BillOfLading": "320845506",
    "TruckNumber": null,
    "TrailerNumber": null,
    "StartTime": "2025-10-10T20:24:35.369Z"
  }
}
```

**What to Look For**:
- TruckNumber is null
- TrailerNumber is null
- Missing BillOfLading
- Invalid carrier identifier

**Common Root Causes**:
- Asset information not provided by carrier
- Truck/Trailer not registered in system
- Operating SCAC not configured
- Asset mapping failure

---

### LR-004: PROCESS_TRUCK_LOCATION (Checkcall Creation)
**Purpose**: Creates Checkcall from location data with geocoding and timezone conversion

**Service**: `global-worker-ex`

**Transmission Types**: BatchLocationsAPI, DispatcherUpdateAPI, EDI 214, Files, LocationsAPI

**Search Keywords**: Mapped Identifier, Permalink

**Shipment Modes**: FTL, TL

**Sample Log**:
```json
{
  "MessageType": "PROCESS_TRUCK_LOCATION",
  "Source": "superfile_ftp",
  "Content": {
    "Carrier": "beemac-trucking-llc",
    "LoadIdentifier": "5642111",
    "Latitude": "33.5103345",
    "Longitude": "-113.01088",
    "LocatedAt": "2025-10-10T16:13:00.000+0000",
    "TruckNumber": "01",
    "TrailerNumber": "002",
    "Mode": "file",
    "TrackingMethod": "location_file"
  },
  "DispatcherApiInfo": {
    "ApiSource": "JustTransform"
  }
}
```

**What to Look For**:
- Invalid coordinates
- Missing LocatedAt timestamp
- Timezone conversion errors
- Geocoding failures
- JustTransform source info

**Common Root Causes**:
- Invalid lat/long values
- Geocoding service failure
- Timezone lookup error
- Missing location timestamp
- JustTransform scraping error

---

### LR-005: PROCESS_NEW_LOCATION (Location Validation)
**Purpose**: Final validation and commit decision for location update

**Service**: `location-worker`

**Transmission Types**: BatchLocationsAPI, DispatcherUpdateAPI, EDI 214, EDIFACT, Files, LocationsAPI

**Search Keywords**: tracking_id

**Shipment Modes**: FTL, TL

**Sample Log**:
```json
{
  "MessageType": "PROCESS_NEW_LOCATION",
  "TrackingId": 626812573,
  "CheckCallParams": {
    "trackingMethod": "truck_number",
    "checkCalls": [{
      "latitude": 37.0982652,
      "longitude": -89.9224512,
      "located_at": "2026-01-18T19:22:51.000+00:00",
      "trackingMethod": "truck_number",
      "provider": "keep-truckin-v2-new",
      "truckNumber": "130"
    }]
  }
}
```

**What to Look For**:
- Location rejected (check reason)
- Duplicate location
- Out-of-sequence location
- Invalid tracking method
- ELD provider issues

**Common Root Causes**:
- Location outside geofence
- Duplicate checkcall
- Location too old
- Invalid tracking asset
- ELD integration error

---

## Root Cause Patterns for TL/FTL

### Pattern 1: File Processing Failure
**Flow**: ProcessSuperFilesTask → PROCESS_SUPER_RECORD

**Symptoms**:
- No PROCESS_SUPER_RECORD after ProcessSuperFilesTask
- File parsing error in ProcessSuperFilesTask
- Missing carrier file

**Investigation**:
1. Search for ProcessSuperFilesTask with filename
2. Check if file format matches carrier config
3. Verify carrier is active
4. Check for file parsing errors

**Common Causes**:
- Malformed CSV/EDI file
- Carrier configuration missing
- File format changed without update
- FTP upload failure

---

### Pattern 2: Asset Assignment Failure
**Flow**: PROCESS_TRUCK_RECORD → (no location updates)

**Symptoms**:
- TruckNumber or TrailerNumber is null in logs
- No PROCESS_TRUCK_LOCATION after PROCESS_TRUCK_RECORD
- "Awaiting Tracking Info" status

**Investigation**:
1. Search for PROCESS_TRUCK_RECORD with LoadIdentifier
2. Check if TruckNumber/TrailerNumber present
3. Verify asset exists in system
4. Check Operating SCAC configuration

**Common Causes**:
- Carrier not sending asset info
- Truck/Trailer not registered
- Operating carrier mismatch
- Asset tracking disabled

---

### Pattern 3: Location Processing Failure
**Flow**: PROCESS_TRUCK_LOCATION → PROCESS_NEW_LOCATION

**Symptoms**:
- No PROCESS_NEW_LOCATION after PROCESS_TRUCK_LOCATION
- Location rejected in PROCESS_NEW_LOCATION
- No checkcalls appearing on load

**Investigation**:
1. Search for PROCESS_TRUCK_LOCATION with LoadIdentifier
2. Check PROCESS_NEW_LOCATION for rejection reason
3. Verify geocoding success
4. Check timezone conversion

**Common Causes**:
- Invalid coordinates
- Location outside allowed radius
- Duplicate location
- Geocoding service down
- Timezone lookup error

---

### Pattern 4: JustTransform/ELD Integration Failure
**Flow**: FETCH_ELD_LOCATION → PROCESS_ELD_LOCATION → PROCESS_NEW_LOCATION

**Symptoms**:
- ApiSource: "JustTransform" in logs
- No locations from ELD provider
- ELD connection errors
- Missing provider credentials

**Investigation**:
1. Search for FETCH_ELD_LOCATION with TrackingID
2. Check JustTransform scraping logs
3. Verify ELD provider credentials
4. Check provider API status

**Common Causes**:
- JustTransform scraping error
- ELD provider portal down
- Invalid credentials
- Provider changed API format
- Rate limiting

---

## SigNoz Query Templates

### Query for File Processing Issues:
```
body CONTAINS "{filename}" AND
body CONTAINS "ProcessSuperFilesTask" AND
deployment.environment = production AND
service.name = carrier-files-worker
```

### Query for Asset Assignment:
```
body CONTAINS "{load_identifier}" AND
body CONTAINS "PROCESS_TRUCK_RECORD" AND
deployment.environment = production AND
service.name = carrier-files-worker
```

### Query for Location Processing:
```
body CONTAINS "{load_identifier}" AND
body CONTAINS "PROCESS_TRUCK_LOCATION" AND
deployment.environment = production AND
service.name = global-worker-ex
```

### Query for Location Validation:
```
body CONTAINS "{tracking_id}" AND
body CONTAINS "PROCESS_NEW_LOCATION" AND
deployment.environment = production AND
service.name = location-worker
```

### Query for ELD/JustTransform:
```
body CONTAINS "{tracking_id}" AND
body CONTAINS "FETCH_ELD_LOCATION" AND
deployment.environment = production AND
service.name = cfw-eld-data
```

---

## Investigation Checklist for TL/FTL Issues

### Step 1: Identify Processing Stage
- [ ] Data Ingestion (ProcessSuperFilesTask)
- [ ] Data Mapping (PROCESS_SUPER_RECORD)
- [ ] Asset Assignment (PROCESS_TRUCK_RECORD)
- [ ] Location Processing (PROCESS_TRUCK_LOCATION)
- [ ] Location Validation (PROCESS_NEW_LOCATION)
- [ ] ELD Integration (FETCH_ELD_LOCATION)

### Step 2: Check Service Logs
- [ ] carrier-files-worker
- [ ] global-worker-ex
- [ ] location-worker
- [ ] global-worker-tracking
- [ ] cfw-eld-data

### Step 3: Verify Data Flow
- [ ] File/API data received?
- [ ] Mapping successful?
- [ ] Assets assigned?
- [ ] Locations created?
- [ ] Locations validated?

### Step 4: Common Failure Points
- [ ] Carrier configuration missing/incorrect
- [ ] File format mismatch
- [ ] Asset info missing (Truck/Trailer)
- [ ] Invalid coordinates
- [ ] JustTransform scraping error
- [ ] ELD provider down
- [ ] Geocoding failure

---

## Recommended Actions by Root Cause

### Carrier Configuration Issue:
- Check carrier permalink in Network Admin
- Verify carrier is active and allow_tracking=true
- Review carrier file format configuration

### File Processing Error:
- Check recent carrier file format changes
- Verify FTP connection and credentials
- Review file parsing configuration

### Asset Assignment Failure:
- Contact carrier for asset information
- Verify truck/trailer exists in system
- Check Operating SCAC configuration

### Location Processing Error:
- Verify coordinates are valid
- Check geocoding service status
- Review timezone conversion logic

### JustTransform/ELD Error:
- Check JustTransform scraping status
- Verify ELD provider credentials
- Check provider API status
- Review rate limiting settings

---

## Key Metrics to Track

1. **File Processing Rate**: ProcessSuperFilesTask → PROCESS_SUPER_RECORD
2. **Asset Assignment Rate**: PROCESS_TRUCK_RECORD with assets vs. without
3. **Location Validation Rate**: PROCESS_NEW_LOCATION accepted vs. rejected
4. **ELD Integration Success**: FETCH_ELD_LOCATION success rate
5. **End-to-End Processing Time**: File ingestion → Location posted

---

## References

- **Log Repository**: Sample Log Repository for Rewind Tool.xlsx
- **Processing Flow**: TL & FTL Processing Flow Diagram
- **Services**: carrier-files-worker, global-worker-ex, location-worker, cfw-eld-data, global-worker-tracking
- **Search Tools**: SigNoz (ClickHouse distributed_logs)
