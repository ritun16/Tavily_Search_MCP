
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