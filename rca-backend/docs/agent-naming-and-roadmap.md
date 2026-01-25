# RCA Agent Naming & Roadmap

Based on Arpit's feedback (Jan 20, 2026)

## Current Agents (Rename)

| Current Name | New Name | Service/Source | Purpose |
|--------------|----------|----------------|---------|
| Redshift Agent | **DWH Agent** | Redshift | Data warehouse queries (load_validation_data_mart, etc.) |
| SigNoz Agent | **Logs Agent** | SigNoz ClickHouse | Service logs with error detection |
| Tracking API Agent | **Tracking Service Agent** | Tracking API | Load metadata, customer-visible data |
| Network Agent | **Network Agent** | Company API | Carrier-shipper relationships |
| Callbacks Agent | **Callbacks Agent** | Athena | Webhook delivery history |
| Super API Agent | **DataHub Agent** | Super API | Ocean tracking configuration |
| JT Agent | **JT Agent** | Just Transform | RPA scraping history (ocean) |
| Confluence Agent | **Confluence Agent** | Confluence | Documentation search |
| JIRA Agent | **JIRA Agent** | JIRA | Related tickets/issues |

## New Agents Needed

### 1. Load File Agent
- **Service**: `integrations-worker`
- **Purpose**: Analyze load file processing errors
- **Log Query**: Search for errors in integrations-worker related to tracking_id
- **Common Issues**:
  - File parsing failures
  - Validation errors during load creation
  - Missing required fields

### 2. Carrier Files Agent
- **Service**: `carrier-files-worker`
- **Purpose**: Analyze carrier file processing pipeline
- **Log Query**: Search for errors in CFW → GWEX → LW flow
- **Common Issues**:
  - Carrier file not received
  - File format errors
  - Processing delays

### 3. Tracking Service Agent (Enhanced)
- **Service**: `tracking-service`
- **Purpose**: API call errors during load creation
- **Log Query**: Search tracking-service logs for 4xx/5xx errors
- **Common Issues**:
  - API validation failures
  - Authentication errors
  - Rate limiting

## Key Log Sources (SigNoz)

```sql
-- integrations-worker errors
SELECT timestamp, body, severity_text, service_name
FROM signoz_logs.logs
WHERE service_name = 'integrations-worker'
  AND severity_text IN ('ERROR', 'WARN')
  AND body LIKE '%{tracking_id}%'
ORDER BY timestamp DESC
LIMIT 50

-- carrier-files-worker errors
SELECT timestamp, body, severity_text, service_name
FROM signoz_logs.logs
WHERE service_name = 'carrier-files-worker'
  AND severity_text IN ('ERROR', 'WARN')
  AND body LIKE '%{tracking_id}%'
ORDER BY timestamp DESC
LIMIT 50

-- tracking-service errors
SELECT timestamp, body, severity_text, service_name
FROM signoz_logs.logs
WHERE service_name = 'tracking-service'
  AND severity_text IN ('ERROR', 'WARN')
  AND body LIKE '%{tracking_id}%'
ORDER BY timestamp DESC
LIMIT 50
```

## Real Issue Patterns (from prod-support channel)

### Pattern 1: Load File Not Processed
- **Symptom**: Load not appearing in system
- **Check**: integrations-worker logs for file processing errors
- **Root Causes**:
  - Invalid file format
  - Missing mandatory fields
  - Duplicate load number

### Pattern 2: Callback Delivery Failure
- **Symptom**: Customer not receiving webhooks
- **Check**: Athena callbacks_v2 for HTTP response codes
- **Root Causes**:
  - Customer endpoint down (4xx/5xx)
  - Network issues
  - Payload too large

### Pattern 3: Carrier Files Not Flowing
- **Symptom**: No position updates from carrier
- **Check**: carrier-files-worker logs, CFW status
- **Root Causes**:
  - Carrier not sending files
  - File parsing errors
  - GWEX mapping issues

## Implementation Priority

1. **Phase 1 (Current)**: Rename existing agents
2. **Phase 2**: Add Load File Agent (integrations-worker)
3. **Phase 3**: Add Carrier Files Agent (carrier-files-worker)
4. **Phase 4**: Enhance Logs Agent with service-specific queries

## Slack Channel Reference
- `#engineering_prod_supp` - Real production issues
- Look for patterns with `tracking_id` mentions
- Focus on ERROR level logs first
