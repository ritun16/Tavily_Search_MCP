
```bash
npx @modelcontextprotocol/inspector uv --directory . run mcp_server_without_header.py
```


```bash
uv pip compile pyproject.toml > requirements.txt
```

### Register Client
```bash
uv run registry_utility.py --server-url http://0.0.0.0:8001 --kid demo-kid-1

uv run registry_utility.py --server-url https://tavily-search-mcp.onrender.com --kid demo-kid-1
```

```
URL: https://tavily-search-mcp.onrender.com/mcp-server/mcp
Label: My_MCP_Server
Origin: https://tavily-search-mcp.onrender.com/mcp-server/mcp
```