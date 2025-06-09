ENV='PROD'

TRUSTED_ORIGINS = [
    "https://tavily-search-mcp.onrender.com/mcp",      # Production trusted origin
    "https://tavily-search-mcp.onrender.com/mcp-server/mcp",
    "http://localhost:8001/mcp",                           # Server localhost URL (FastAPI server)
    "http://localhost:8001/mcp-server/mcp",
    "http://0.0.0.0:8001/mcp",
    "http://0.0.0.0:8001/mcp-server/mcp",
]