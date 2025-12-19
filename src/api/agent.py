from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models.users import User
# from app.utils.subscription import require_active_subscription
from src.utils.auth_dependencies import get_current_user
from src.agents.agent import agent
from src.agents.context import context

router = APIRouter(prefix="/agent", tags=["AI-Agent"])

class AgentRequest(BaseModel):
    query: str

@router.post("/ask")
async def ask_agent(request: AgentRequest, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    context.user_id = current_user.id

    result = agent.invoke({
        "messages": [{"role": "user", "content": request.query}]
    })

    # Last AI Message
    ai_msg = result["messages"][-1]

    content = ai_msg.content

    # Convert structured messages → plain text
    if isinstance(content, list):
        content = content[0].get("text", "")

    return {"response": content}