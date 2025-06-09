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
    



from fastmcp.server.auth.providers.bearer import RSAKeyPair

# Generate a fresh key pair (for dev/testing only!)
key_pair = RSAKeyPair.generate()

# Extract the PEM-encoded public and private keys
private_pem = key_pair.private_key
public_pem = key_pair.public_key

print("PUBLIC KEY:\n", public_pem)
print("PRIVATE KEY:\n", private_pem)
