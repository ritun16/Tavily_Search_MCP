import os
import json
import threading
from datetime import datetime
from typing import Annotated, Literal, List
from colorama import Fore, Style

import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends, Body
from fastapi.responses import JSONResponse
from starlette.requests import Request

from pydantic import BaseModel, Field, field_validator

from cryptography.hazmat.primitives import serialization
from jwcrypto import jwk

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.dependencies import get_http_request
from fastmcp.exceptions import FastMCPError

from mcp.types import (
    ErrorData,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from tavily import (
    AsyncTavilyClient,
    InvalidAPIKeyError,
    UsageLimitExceededError,
)

from config import ENV, TRUSTED_ORIGINS


# ———— 1) A custom class to validate MCP client requests ————

class MCPSecurityValidator:
    """
    Utility class for validating security aspects of incoming MCP client requests.
    Handles origin validation, server bind address selection, and Tavily API key extraction.
    """

    def validate_origin(self, request: Request) -> bool:
        """
        Validates that the request's Origin header is present and is in the list of trusted origins.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            bool: True if the origin is valid.

        Raises:
            ValueError: If the Origin header is missing or not trusted.
        """
        origin = request.headers.get("Origin")
        if origin is None or origin not in TRUSTED_ORIGINS:
            raise ValueError("Invalid or missing Origin header")
        return True

    def validate_bind(self) -> str:
        """
        Determines the server bind address based on the environment.

        Returns:
            str: The IP address to bind the server to.
                 "0.0.0.0" for deployment, "127.0.0.1" for local development.
        """
        if ENV == "PROD":
            return "0.0.0.0"
        else:
            return "127.0.0.1"

    def get_tavily_api_key(self, request: Request) -> str:
        """
        Extracts and returns the Tavily API key from the request headers.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            str: The Tavily API key.

        Raises:
            ValueError: If the Tavily-API-Key header is missing.
        """
        tavily_api_key_header = request.headers.get("Tavily-API-Key")
        if tavily_api_key_header is None:
            raise ValueError("Invalid or missing Tavily-API-Key header")
        return tavily_api_key_header.strip()

# A singleton instance of the security validator
mcp_security_validator = MCPSecurityValidator()


# ———— 2) A PyDantic model for the MCP server tools ————
class WebSearch(BaseModel):
    """Parameters for general web search."""

    query: Annotated[str, Field(description="Search query")]
    max_results: Annotated[
        int,
        Field(
            default=3, description="Maximum number of results to return", gt=0, lt=20
        ),
    ]
    search_depth: Annotated[
        Literal["basic", "advanced"],
        Field(default="basic", description="Depth of search - 'basic' or 'advanced'"),
    ]
    include_domains: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="List of domains to specifically include in the search results (e.g. ['example.com', 'test.org'] or 'example.com')",
        ),
    ]
    exclude_domains: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="List of domains to specifically exclude from the search results (e.g. ['example.com', 'test.org'] or 'example.com')",
        ),
    ]
    days: Annotated[
        int | None,
        Field(
            default=7,
            description="Number of days back to search (default is 7)",
            gt=0,
            le=365,
        ),
    ]

    @field_validator("include_domains", "exclude_domains", mode="before")
    @classmethod
    def parse_domains_list(cls, v):
        # Ref : Tavily MCP
        if v is None:
            return []
        if isinstance(v, list):
            return [domain.strip() for domain in v if domain.strip()]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            try:
                # Try to parse as JSON string
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [domain.strip() for domain in parsed if domain.strip()]
                return [parsed.strip()]  # Single value from JSON
            except json.JSONDecodeError:
                # Not JSON, check if comma-separated
                if "," in v:
                    return [domain.strip() for domain in v.split(",") if domain.strip()]
                return [v]  # Single domain
        return []


# ———— 3) A thread-safe in-memory registry of client public PEMs ————

class PublicKeyRegistry:
    """
    Thread-safe in-memory registry for storing client public PEM keys and their associated Key IDs (kid).
    This registry is used to manage the set of public keys that are allowed to authenticate with the server.
    """

    def __init__(self):
        # Lock to ensure thread-safe access to the registry
        self._lock = threading.Lock()
        # List to store dictionaries of the form {"pem": <public_key_pem>, "kid": <key_id>}
        self._pems: List[dict] = []

    def add_pem(self, pem: str, kid: str):
        """
        Add a new PEM-encoded public key and its key ID to the registry.
        Ensures that duplicate (pem, kid) pairs are not added.
        
        Args:
            pem (str): The PEM-encoded public key.
            kid (str): The key ID associated with the public key.
        """
        with self._lock:
            present = False

            for pem_dict in self._pems:
                if pem_dict["pem"] == pem or pem_dict["kid"] == kid:
                    present = True  # Duplicate found
            if not present:
                self._pems.append({"pem": pem, "kid": kid})
                return True, False # True, False means (Key added successfully and the key or kid was not present)
            else:
                return True, True # True, True means (Key added successfully and the key or kid was present)

    def as_jwks(self):
        """
        Returns the registry as a JWKS (JSON Web Key Set) dictionary.
        Each registered PEM is converted to a JWK and included in the set.
        
        Returns:
            dict: A dictionary with a "keys" field containing the list of JWKs.
        """
        keys = []
        for pem_dict in self._pems:
            # Load the public key from PEM
            key_obj = serialization.load_pem_public_key(pem_dict["pem"].encode())
            # Convert the public key to a JWK using jwcrypto
            jwk_key = jwk.JWK.from_pyca(key_obj)
            jwk_key_json = json.loads(jwk_key.export_public())
            # Attach the correct key ID (kid)
            jwk_key_json["kid"] = pem_dict["kid"]
            keys.append(jwk_key_json)
        return {"keys": keys}

# A singleton instance of the public key registry
registry = PublicKeyRegistry()

# ———— 4) Wire up FastMCP with that JWKS endpoint ————
MCP_SERVER_URL = f"http://{mcp_security_validator.validate_bind()}:{os.environ.get('PORT', 8001)}"
JWKS_URL = f"{MCP_SERVER_URL}/.well-known/jwks.json"

auth = BearerAuthProvider(
    jwks_uri=JWKS_URL,
)

# ———— 5) Declare MCP server with Authentication ————
mcp = FastMCP(name="Multi‐client MCP Server", auth=auth)

# ———— 6) FastAPI app ————
mcp_app = mcp.http_app(path="/mcp")
app = FastAPI(lifespan=mcp_app.lifespan)


# ———— 7) Register client endpoint ————
@app.post("/register-client")
async def register_client(public_key_pem: str = Body(...), kid: str = Body(...)):
    """
    Register client endpoint: supply a PEM‐encoded public key, get it registered.
    """
    try:
        # validate it actually parses
        serialization.load_pem_public_key(public_key_pem.encode())
    except Exception:
        raise HTTPException(400, "Invalid PEM")

    is_key_added, is_key_present = registry.add_pem(public_key_pem, kid)
    if is_key_added:
        if is_key_present:
            return {"status": "error", "message": "Key or KID already registered. Try again with different KID."}
        else:
            return {"status": "ok", "registered_keys": len(registry._pems), "message": "Key registered successfully"}
    else:
        raise HTTPException(400, "Failed to add key")

# ———— 8) JWKS endpoint ————
@app.get("/.well-known/jwks.json")
async def get_jwks():
    """
    Exposes the JWKS set for all registered client keys.
    """
    return JSONResponse(registry.as_jwks())

# ———— 9) MCP server tools ————
@mcp.tool
async def general_search(web_search_args: WebSearch) -> str:
    """
    Performs a general web search using the Tavily API and returns results.

    This function conducts an search query using Tavily's search API, retrieving both URLs and raw content
    from the search results. The results are formatted as a string containing URLs and their corresponding content.

    Args:
        web_search_args (WebSearch): The search argument which is a pydantic class

    Returns:
        str: A formatted string containing search results, with each result showing:
             - Search URL: The URL of the search result
             - Search Content: The raw content from that URL
    """

    print(f"General Search Started with Args: {web_search_args.model_dump_json()}")

    # Process the request from the client
    request: Request = get_http_request()

    # Validate the request
    mcp_security_validator.validate_origin(request)

    # Fetch the Tavily API Key from the header
    tavily_api_key = mcp_security_validator.get_tavily_api_key(request)

    try:
        tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        search_result = await tavily_client.search(
            query=web_search_args.query,
            topic="general",
            search_depth=web_search_args.search_depth,
            include_raw_content=True,
            include_answer=True,
            max_results=web_search_args.max_results,
            include_domains=web_search_args.include_domains,
            exclude_domains=web_search_args.exclude_domains,
        )

        # Format the result
        formatted_results = ""
        result_index = 1
        for result in search_result["results"]:
            search_url = result["url"]
            search_raw_content = result["raw_content"]
            if search_url and search_raw_content:
                formatted_results += (
                    f"{Fore.GREEN}----------------- Result: {result_index} -----------------{Style.RESET_ALL}\n"
                )
                formatted_results += (
                    f"{Fore.BLUE}Search URL: {search_url}{Style.RESET_ALL}\n"
                )
                formatted_results += (
                    f"{Fore.YELLOW}Search Content: {search_raw_content}{Style.RESET_ALL}\n\n"
                )
                result_index += 1
    except (InvalidAPIKeyError, UsageLimitExceededError) as erroe:
        raise FastMCPError(ErrorData(code=INTERNAL_ERROR, message=str(erroe)))
    except ValueError as error:
        raise FastMCPError(ErrorData(code=INVALID_PARAMS, message=str(error)))

    print(formatted_results)
    return formatted_results


# ———— 10) MCP server tools ————
@mcp.tool()
async def news_search(web_search_args: WebSearch) -> str:
    """
    Performs a news search using the Tavily API and returns results.

    This function conducts a news search query using Tavily's search API, retrieving both URLs and raw content
    from the search results. The results are formatted as a string containing URLs and their corresponding content.

    Args:
        web_search_args (WebSearch): The search argument which is a pydantic class

    Returns:
        str: A formatted string containing search results, with each result showing:
             - Search URL: The URL of the search result
             - Search Content: The raw content from that URL
    """

    print(f"News Search Started with Args: {web_search_args.model_dump_json()}")

    # Process the request from the client
    request: Request = get_http_request()

    # Validate the request
    mcp_security_validator.validate_origin(request)

    # Fetch the Tavily API Key from the header
    tavily_api_key = mcp_security_validator.get_tavily_api_key(request)

    try:
        tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        search_result = await tavily_client.search(
            query=web_search_args.query,
            topic="news",
            search_depth=web_search_args.search_depth,
            include_raw_content=True,
            include_answer=True,
            max_results=web_search_args.max_results,
            include_domains=web_search_args.include_domains,
            exclude_domains=web_search_args.exclude_domains,
            days=web_search_args.days,
        )

        # Format the result
        formatted_results = ""
        result_index = 1
        for result in search_result["results"]:
            search_url = result["url"]
            search_raw_content = result["raw_content"]
            if search_url and search_raw_content:
                formatted_results += (
                    f"{Fore.GREEN}----------------- Result: {result_index} -----------------{Style.RESET_ALL}\n"
                )
                formatted_results += (
                    f"{Fore.BLUE}Search URL: {search_url}{Style.RESET_ALL}\n"
                )
                formatted_results += (
                    f"{Fore.YELLOW}Search Content: {search_raw_content}{Style.RESET_ALL}\n\n"
                )
                result_index += 1
    except (InvalidAPIKeyError, UsageLimitExceededError) as erroe:
        raise FastMCPError(ErrorData(code=INTERNAL_ERROR, message=str(erroe)))
    except ValueError as error:
        raise FastMCPError(ErrorData(code=INVALID_PARAMS, message=str(error)))

    print(formatted_results)
    return formatted_results


# ———— 11) Mount the MCP server ————
app.mount("/mcp-server", mcp_app)

if __name__ == "__main__":
    uvicorn.run(app, host=f"{mcp_security_validator.validate_bind()}", port=int(os.environ.get("PORT", 8001)))
