
```bash
npx @modelcontextprotocol/inspector uv --directory . run mcp_server_without_header.py
```

```json
{
  "query": "Did South African president Cyril Ramaphosa visit USA to meet donald trump in recent past?",
  "max_results": 3,
  "search_depth": "basic",
  "include_domains": null,
  "exclude_domains": null,
  "days": 365
}
```

```bash
uv pip compile pyproject.toml > requirements.txt
```

```
# sample_query = "What is model context protocol?"
# sample_query = "What is the GDP of Madagascar?"
# sample_query = "What is OSS in IT or software engineering?"
# sample_query = "What is the score of England vs Zimbabwe for the ongoing test match?"
# sample_query = "Did South African president Cyril Ramaphosa visit USA to meet donald trump in recent past?"
# sample_query = "What was the reason for recent stampede at bangalore?"
```

### Register Client
```bash
uv run register_client.py --server-url http://0.0.0.0:8001 --kid demo-kid-1

uv run register_client.py --server-url https://tavily-search-mcp.onrender.com --kid demo-kid-1
```