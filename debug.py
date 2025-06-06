from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.thinking import ThinkingTools

reasoning_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[ThinkingTools(add_instructions=True)],
    instructions="You are a helpful assistant that can think and reason about the user's question.",
)



if __name__ == "__main__":
    reasoning_agent.print_response("How many S are there in Mississippi?",
                                         show_full_reasoning=True)
    

