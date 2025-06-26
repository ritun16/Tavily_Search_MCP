# from agno.agent import Agent
# from agno.models.openai import OpenAIChat
# from agno.tools.thinking import ThinkingTools

# reasoning_agent = Agent(
#     model=OpenAIChat(id="gpt-4o-mini"),
#     tools=[ThinkingTools(add_instructions=True)],
#     instructions="You are a helpful assistant that can think and reason about the user's question.",
# )



# if __name__ == "__main__":
#     reasoning_agent.print_response("How many S are there in Mississippi?",
#                                          show_full_reasoning=True)
    

# import asyncio
# import os
# from tavily import (
#     AsyncTavilyClient,
#     InvalidAPIKeyError,
#     UsageLimitExceededError,
# )
# from dotenv import load_dotenv

# load_dotenv(".env.dev")

# tavily_api_key = os.getenv("TAVILY_API_KEY")
# # {"query":"ITR 2 changes India 2025","max_results":3,"search_depth":"basic","include_domains":null,"exclude_domains":null,"days":7}
# async def main():
#     tavily_client = AsyncTavilyClient(api_key=tavily_api_key)

#     search_result = await tavily_client.search(
#                 query="ITR 2 changes India 2025",
#                 topic="general",
#                 search_depth="basic",
#                 include_raw_content=True,
#                 include_answer=False,
#                 max_results=1,
#                 include_domains=None,
#                 exclude_domains=None,
#             )
#     print(search_result["results"][0]['content'])

# if __name__ == "__main__":
#     asyncio.run(main())

