# Setup Redshift MCP for Claude Desktop

## Step 1: Verify MCP Server is Built

```bash
cd /Users/msp.raja/agent-cassie/investigation-agent/mcp-server-redshift
npm install
npm run build
```

This should create the `dist/index.js` file.

## Step 2: Locate Claude Desktop Config File

The Claude Desktop configuration file is located at:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

## Step 3: Add Redshift MCP Configuration

Open the config file and add the Redshift MCP server configuration:

```json
{
  "mcpServers": {
    "redshift": {
      "command": "node",
      "args": [
        "/Users/msp.raja/agent-cassie/investigation-agent/mcp-server-redshift/dist/index.js"
      ],
      "env": {
        "REDSHIFT_HOST": "productiondwh.c5iyekvfm1hi.us-east-1.redshift.amazonaws.com",
        "REDSHIFT_PORT": "5439",
        "REDSHIFT_DATABASE": "productiondwh",
        "REDSHIFT_USER": "fkin10365",
        "REDSHIFT_PASSWORD": "H3r*3^tyC3Bh",
        "REDSHIFT_SCHEMAS": "public,hadoop",
        "TRANSPORT_TYPE": "stdio"
      }
    }
  }
}
```

**Note:** If you already have other MCP servers configured, merge this into your existing `mcpServers` object.

## Step 4: Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Step 5: Verify Connection

In Claude Desktop, you should now be able to use Redshift queries:

**Example queries:**
- "List all tables in the public schema"
- "Show me data for Amazon from the data warehouse"
- "Query company_licensing_packages table for Baxter"

## Available Tools

Once configured, Claude Desktop will have access to these Redshift tools:

1. **list_tables** - List all available tables
2. **get_table_schema** - Get column details for a table
3. **execute_query** - Run SQL queries
4. **list_schemas** - List available database schemas

## Troubleshooting

### MCP Server Not Starting

Check the Claude Desktop logs:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

### Connection Errors

Ensure you're connected to FourKites VPN/network. The Redshift cluster is only accessible from within the FourKites network.

### Build Errors

If the MCP server isn't built:
```bash
cd /Users/msp.raja/agent-cassie/investigation-agent/mcp-server-redshift
rm -rf dist node_modules package-lock.json
npm install
npm run build
```

## Security Note

The configuration file contains database credentials. Ensure:
- File permissions are restricted (Claude Desktop handles this automatically)
- Don't commit this config to version control
- Don't share the config file

## Query Results

The query we just ran found:
- ✅ **Amazon** - Found in company_licensing_packages
- ✅ **Arrow Electronics** - Found in multiple tables
- ✅ **Baxter EMEA** (as Baxter International) - Found in company_licensing_packages
- ✅ **Beacon Building Products** (as Beacon Transport) - Found in company_licensing_packages
- ✅ **Becton Dickinson** (as JDA Becton Dickinson) - Found in company_licensing_packages
- ❌ **Ahold Delhaize** - Not found in checked tables
- ❌ **BASF** - Not found in checked tables

You can now run more detailed queries through Claude Desktop MCP to get full prospect data!
