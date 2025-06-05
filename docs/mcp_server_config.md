# MCP Server Configuration

This document shows how to connect VS Code or other MCP-compatible clients to the
`CryptoMamba` server implemented in `mcp_server.py`.

## Example `mcp.json`

Place a file named `mcp.json` in your project or workspace and add an entry for
this server. When the MCP extension starts, it will read this configuration and
launch the server.

```json
{
  "servers": {
    "crypto-mamba": {
      "type": "streamable-http",
      "command": "python",
      "args": ["mcp_server.py"],
      "url": "http://localhost:8000"
    }
  }
}
```

### Prompted Inputs

If your tools require API keys or other credentials, you can add them under
`inputs` to have VS Code securely prompt for them on first start.

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "perplexity-key",
      "description": "Perplexity API Key",
      "password": true
    }
  ]
}
```

Combine these sections as needed to connect multiple servers.
