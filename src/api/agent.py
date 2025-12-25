from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models.users import User
from src.utils.subscription import require_active_subscription
# from src.utils.auth_dependencies import get_current_user
from src.agents.agent import agent
from src.agents.agent_state import AgentState
from src.utils.agent_dependencies import get_agent_state

router = APIRouter(prefix="/agent", tags=["AI-Agent"])

class AgentRequest(BaseModel):
    query: str
    document_id: int | None = None

@router.post("/ask")
async def ask_agent(
    request: AgentRequest,
    state: AgentState = Depends(get_agent_state),
    current_user: User = Depends(require_active_subscription)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Attach user to state
    state.user_id = current_user.id

    state.active_document_id = request.document_id

    # Save user message
    state.chat_history.append({
        "role": "user",
        "content": request.query
    })
    state.last_query = request.query

    # Sliding window
    MAX_TURNS = 5
    state.chat_history = state.chat_history[-MAX_TURNS:]

    # Inject memory into agent
    result = agent.invoke(
        {
            "messages": state.chat_history
        },
        config={
            "configurable": {
                "agent_state": state
            }
        }
    )

    # Extract assistant reply
    ai_msg = result["messages"][-1]
    content = ai_msg.content

    if isinstance(content, list):
        content = content[0].get("text", "")

    # Save assistant reply to memory
    state.chat_history.append({
        "role": "assistant",
        "content": content
    })

    return {"response": content}