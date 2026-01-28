a # Available MCP Servers

## Currently Configured in Claude Desktop

### ✅ 1. Redshift MCP Server
**Location:** `/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-redshift/`
**Status:** ✅ Configured in Claude Desktop
**Purpose:** Amazon Redshift database queries and analytics

**Tools Available:**
- `list_tables` - List all tables in configured schemas
- `get_tables_schema` - Get column details for specific tables
- `query` - Execute SQL queries against Redshift

**Configuration:**
```json
{
  "REDSHIFT_HOST": "productiondwh.c5iyekvfm1hi.us-east-1.redshift.amazonaws.com",
  "REDSHIFT_PORT": "5439",
  "REDSHIFT_DATABASE": "productiondwh",
  "REDSHIFT_SCHEMAS": "public,hadoop"
}
```

**Use Cases:**
- Query prospect company data
- Access production data warehouse
- Run analytics on shipment data
- Search for customer/shipper information

---

### 2. n8n MCP Server
**Location:** `/Users/msp.raja/n8n-mcp-server/`
**Status:** ✅ Previously configured in Claude Desktop (removed when Redshift was added)
**Purpose:** n8n workflow automation management

**Tools Available:**
- **Workflow Management:**
  - `list_workflows` - List all workflows
  - `get_workflow` - Get workflow details
  - `create_workflow` - Create new workflow
  - `update_workflow` - Update existing workflow
  - `delete_workflow` - Delete workflow
  - `activate_workflow` - Activate workflow
  - `deactivate_workflow` - Deactivate workflow

- **Execution Control:**
  - `execute_workflow` - Execute workflow
  - `get_executions` - Get execution history
  - `get_execution` - Get specific execution details
  - `delete_execution` - Delete execution record
  - `retry_execution` - Retry failed execution

- **Tag & Search:**
  - `get_tags` - List all tags
  - `create_tag` - Create new tag
  - `search_workflows` - Search by name/tags
  - `get_workflow_webhooks` - Get webhook URLs

**Configuration:**
```json
{
  "N8N_URL": "http://localhost:5678",
  "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Use Cases:**
- Automate workflows
- Create integration pipelines
- Manage n8n workflows via natural language
- Execute and monitor automation tasks

---

## Available in Agent Cassie (Not in Claude Desktop)

### 3. Salesforce MCP Server
**Location:** `/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-salesforce/`
**Status:** ⚠️ Built but not in Claude Desktop
**Purpose:** Salesforce CRM data and case management

**Capabilities:**
- Query Salesforce cases
- Get account details
- Retrieve case attachments
- AI-powered file analysis (screenshots, PDFs)
- Case field metadata access

**To Add to Claude Desktop:**
```json
{
  "salesforce": {
    "command": "node",
    "args": [
      "/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-salesforce/dist/index.js"
    ],
    "env": {
      "SALESFORCE_LOGIN_URL": "https://fourkites.my.salesforce.com",
      "SALESFORCE_USERNAME": "your-username",
      "SALESFORCE_PASSWORD": "your-password",
      "AWS_BEDROCK_ACCESS_KEY": "your-key",
      "AWS_BEDROCK_SECRET_KEY": "your-secret"
    }
  }
}
```

**Use Cases:**
- Query support cases
- Get customer account information
- Analyze case attachments
- Search for specific tickets

---

### 4. Knowledge MCP Server
**Location:** `/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-knowledge/`
**Status:** ⚠️ Built but not in Claude Desktop
**Purpose:** Internal knowledge base search

**Use Cases:**
- Search internal documentation
- Find troubleshooting guides
- Access best practices
- Query knowledge articles

**To Add to Claude Desktop:**
```json
{
  "knowledge": {
    "command": "node",
    "args": [
      "/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-knowledge/dist/index.js"
    ],
    "env": {
      "KNOWLEDGE_BASE_URL": "your-kb-url",
      "KNOWLEDGE_API_KEY": "your-api-key"
    }
  }
}
```

---

### 5. Support AI MCP Server
**Location:** `/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-support-ai/`
**Status:** ⚠️ Built but not in Claude Desktop
**Purpose:** FourKites API integrations (Tracking API, Network API, Company API)

**Capabilities:**
- Tracking API queries (load search, status)
- Network API queries (relationships, ELD config)
- Company API queries (settings, configuration)
- Login support tools
- User management

**To Add to Claude Desktop:**
```json
{
  "support-ai": {
    "command": "node",
    "args": [
      "/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-support-ai/dist/index.js"
    ],
    "env": {
      "FOURKITES_API_KEY": "your-api-key",
      "TRACKING_API_URL": "your-tracking-api-url",
      "NETWORK_API_URL": "your-network-api-url"
    }
  }
}
```

**Use Cases:**
- Query load tracking status
- Check network relationships
- Verify company configurations
- User authentication support

---

## Additional MCP Servers (Mentioned in Agent Cassie)

### 6. Atlassian MCP Server
**Status:** 📝 Mentioned in documentation, location unknown
**Purpose:** Jira and Confluence integration

**Capabilities:**
- Search Confluence pages
- Query JIRA issues
- Access internal documentation
- Find technical guides

---

## Summary

| MCP Server | Status | Location | In Claude Desktop |
|------------|--------|----------|-------------------|
| **Redshift** | ✅ Ready | agent-cassie/investigation-agent/mcp-server-redshift | ✅ Yes |
| **n8n** | ✅ Ready | n8n-mcp-server | ❌ No (was configured, removed) |
| **Salesforce** | ⚠️ Built | agent-cassie/investigation-agent/mcp-server-salesforce | ❌ No |
| **Knowledge** | ⚠️ Built | agent-cassie/investigation-agent/mcp-server-knowledge | ❌ No |
| **Support AI** | ⚠️ Built | agent-cassie/investigation-agent/mcp-server-support-ai | ❌ No |
| **Atlassian** | 📝 Mentioned | Unknown | ❌ No |

---

## Quick Add Commands

To add any of these to Claude Desktop, edit:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

And add the corresponding configuration block to the `"mcpServers"` section.

**Note:** Make sure to build each MCP server first:
```bash
cd /path/to/mcp-server
npm install
npm run build
```

---

## What You Can Do Now

**With Redshift MCP (active):**
- Query prospect companies: "Find Amazon in the data warehouse"
- Search company data: "Show me all companies with 'Baxter' in their name"
- Run analytics: "Query shipment metrics for top customers"

**To Enable More:**
1. Add Salesforce MCP → Query support cases
2. Add Support AI MCP → Check load tracking, network configs
3. Add Knowledge MCP → Search internal documentation
4. Add n8n MCP back → Automate workflows

Just let me know which ones you want added!
