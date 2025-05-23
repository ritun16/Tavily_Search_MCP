import asyncio
import os
import json

from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from fastmcp.exceptions import FastMCPError
from starlette.requests import Request

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


# Define the MCP server
web_search_mcp_server = FastMCP(
    "Web Search",
    port=int(os.environ.get("PORT", 8001)),
    host="0.0.0.0",
    stateless_http=True,
)

# Define the search schema


class WebSearch(BaseModel):
    """Parameters for general web search."""

    query: Annotated[str, Field(description="Search query")]
    max_results: Annotated[int, Field(default=3, description="Maximum number of results to return", gt=0, lt=20)]
    search_depth: Annotated[Literal["basic", "advanced"], Field(default="basic", description="Depth of search - 'basic' or 'advanced'")]
    include_domains: Annotated[list[str] | None, Field(default=None, description="List of domains to specifically include in the search results (e.g. ['example.com', 'test.org'] or 'example.com')")]
    exclude_domains: Annotated[list[str] | None, Field(default=None, description="List of domains to specifically exclude from the search results (e.g. ['example.com', 'test.org'] or 'example.com')")]
    days: Annotated[int | None, Field(default=7, description="Number of days back to search (default is 3)", gt=0, le=365)]

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


# Utility function for getting the token
def get_tavily_api_key(request: Request):
    headers = request.headers
    # Check if 'Authorization' header is present
    authorization_header = headers.get('Tavily-API-Key')
    
    if authorization_header:
        return authorization_header.strip()
    else:
        raise ValueError("Authorization header missing")
    

# General Search
@web_search_mcp_server.tool()
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

    # Fetch the Tavily API Key from the header
    tavily_api_key = get_tavily_api_key(request)

    try:
        tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        search_result = await tavily_client.search(
                                query=web_search_args.query,
                                topic="general",
                                search_depth=web_search_args.search_depth,
                                include_raw_content=False,
                                include_answer=True,
                                max_results=web_search_args.max_results,
                                include_domains=web_search_args.include_domains,
                                exclude_domains=web_search_args.exclude_domains,
                            )
        
        # Format the result
        formatted_results = ""
        result_index = 1
        for result in search_result['results']:
            search_url = result['url']
            search_raw_content = result['content']
            if search_url and search_raw_content:
                formatted_results += f"----------------- Result: {result_index} -----------------\n"
                formatted_results += f"Search URL: {search_url}\nSearch Content: {search_raw_content}\n\n"
                result_index += 1
    except (InvalidAPIKeyError, UsageLimitExceededError) as erroe:
        raise FastMCPError(ErrorData(code=INTERNAL_ERROR, message=str(erroe)))
    except ValueError as error:
        raise FastMCPError(ErrorData(code=INVALID_PARAMS, message=str(error)))
    
    return formatted_results


# News Search
@web_search_mcp_server.tool()
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

    # Fetch the Tavily API Key from the header
    tavily_api_key = get_tavily_api_key(request)

    try:
        tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        search_result = await tavily_client.search(
                                query=web_search_args.query,
                                topic="news",
                                search_depth=web_search_args.search_depth,
                                include_raw_content=False,
                                include_answer=True,
                                max_results=web_search_args.max_results,
                                include_domains=web_search_args.include_domains,
                                exclude_domains=web_search_args.exclude_domains,
                                days=web_search_args.days,
                            )
        
        # Format the result
        formatted_results = ""
        result_index = 1
        for result in search_result['results']:
            search_url = result['url']
            search_raw_content = result['content']
            if search_url and search_raw_content:
                formatted_results += f"----------------- Result: {result_index} -----------------\n"
                formatted_results += f"Search URL: {search_url}\nSearch Content: {search_raw_content}\n\n"
                result_index += 1
    except (InvalidAPIKeyError, UsageLimitExceededError) as erroe:
        raise FastMCPError(ErrorData(code=INTERNAL_ERROR, message=str(erroe)))
    except ValueError as error:
        raise FastMCPError(ErrorData(code=INVALID_PARAMS, message=str(error)))
    
    return formatted_results


async def main():
    await web_search_mcp_server.run_async(transport="streamable-http")

if __name__ == "__main__":
    asyncio.run(main())