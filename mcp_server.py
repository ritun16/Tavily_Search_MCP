import os

from tavily import TavilyClient
# from mcp.server.fastmcp import FastMCP, Context
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Web Search", port=8001, stateless_http=True)

def get_tavily_api_key(request: Request):
    headers = request.headers
    # Check if 'Authorization' header is present
    authorization_header = headers.get('TavilyAPIKey')
    
    if authorization_header:
        # Split the header into 'Bearer <token>'
        parts = authorization_header.split()
        
        if len(parts) == 2 and parts[0] == 'Bearer':
            return parts[1]
        else:
            raise ValueError("Invalid Authorization header format")
    else:
        raise ValueError("Authorization header missing")


@mcp.tool()
def search_general(query: str) -> str:
    """
    Performs a general web search using the Tavily API and returns results.
    
    This function conducts an advanced search query using Tavily's search API, retrieving both URLs and raw content
    from the search results. The results are formatted as a string containing URLs and their corresponding content.
    
    Args:
        query (str): The search query string to look up
        
    Returns:
        str: A formatted string containing search results, with each result showing:
             - Search URL: The URL of the search result
             - Search Content: The raw content from that URL
    """
    request: Request = get_http_request()
    tavily_api_key = get_tavily_api_key(request)
    tavily_client = TavilyClient(api_key=tavily_api_key)
    search_result = tavily_client.search(
                                query=query,
                                topic="general",
                                search_depth="advanced",
                                include_raw_content=False,
                                include_answer=True,
                                max_results=3,
                            )
    return_results = ""
    result_index = 1
    for result in search_result['results']:
        search_url = result['url']
        search_raw_content = result['content']
        if search_url and search_raw_content:
            return_results += f"----------------- Result: {result_index} -----------------\n"
            return_results += f"Search URL: {search_url}\nSearch Content: {search_raw_content}\n\n"
            result_index += 1
    
    return return_results

@mcp.tool()
def search_news(query: str) -> str:
    """
    Performs a news search using the Tavily API and returns results.
    
    This function conducts an advanced news search query using Tavily's search API, retrieving both URLs and raw content
    from recent news articles. The results are formatted as a string containing URLs and their corresponding content.
    
    Args:
        query (str): The news search query string to look up
        
    Returns:
        str: A formatted string containing news search results, with each result showing:
             - Search URL: The URL of the news article
             - Search Content: The raw content from that news article
    """
    request: Request = get_http_request()
    tavily_api_key = get_tavily_api_key(request)
    tavily_client = TavilyClient(api_key=tavily_api_key)
    search_result = tavily_client.search(
                                query=query,
                                topic="news",
                                search_depth="basic",
                                time_range="month",
                                include_raw_content=False,
                                include_answer=True,
                                max_results=5,
                            )
    return_results = ""
    result_index = 1
    for result in search_result['results']:
        search_url = result['url']
        search_raw_content = result['content']
        if search_url and search_raw_content:
            return_results += f"----------------- Result: {result_index} -----------------\n"
            return_results += f"Search URL: {search_url}\nSearch Content: {search_raw_content}\n\n"
            result_index += 1
    
    return return_results

# async def main():
#     general_query = "What is Model Context Protocol?"
#     news_query = "What is the current tarrif condition of the USA?"
#     general_results = search_general(general_query)
#     news_results = search_news(news_query)
#     print(general_results)
#     print(news_results)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")