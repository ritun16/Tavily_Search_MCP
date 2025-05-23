import asyncio
import os
from tavily import (
    AsyncTavilyClient,
    InvalidAPIKeyError,
    UsageLimitExceededError,
)

from dotenv import load_dotenv

load_dotenv(".env.dev")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

async def search():
    # {"query":"England vs Zimbabwe test match score","max_results":1,"search_depth":"basic","include_domains":null,"exclude_domains":null,"days":null}
    tavily_client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
    search_result = await tavily_client.search(
                                query="England vs Zimbabwe test match score",
                                topic="news",
                                search_depth="basic",
                                include_raw_content=False,
                                include_answer=True,
                                max_results=1,
                                include_domains=None,
                                exclude_domains=None,
                                days=1,
                            )
    print(search_result)

if __name__ == "__main__":
    asyncio.run(search())