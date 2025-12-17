from src.agents.context import context
from langchain_core.messages import HumanMessage

def agent_context_middleware(agent):
    def run(user_input: str):
        """
        Middleware-controlled execution loop
        """
        # Safety: reset context only if query changes domain
        if context.last_query and user_input != context.last_query:
            # keep docs unless user intent clearly changes
            pass

        result = agent.invoke({
            "messages": [HumanMessage(content=user_input)]
        })

        return result

    return run