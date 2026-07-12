from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage, ToolMessage
from app.langgraph.workflow import graph
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AgentChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentChatResponse(BaseModel):
    response: str
    extracted_data: Optional[Dict[str, Any]] = None
    tool_used: Optional[str] = None

@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(data: AgentChatRequest):
    try:
        initial_state = {
            "messages": [HumanMessage(content=data.message)],
            "extracted_data": {}
        }

        result = graph.invoke(initial_state)
        messages = result.get("messages", [])

        # Extract the final AI text response (last non-tool message)
        final_response = "I've processed your request."
        for msg in reversed(messages):
            msg_type = type(msg).__name__
            if msg_type == "AIMessage":
                content = msg.content
                if isinstance(content, str) and content.strip():
                    final_response = content
                    break
                elif isinstance(content, list):
                    # Handle list-type content (some models return list)
                    text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    combined = " ".join(text_parts).strip()
                    if combined:
                        final_response = combined
                        break

        # Extract tool results
        extracted_data: Dict[str, Any] = {}
        tool_used: Optional[str] = None

        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_used = msg.name
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict):
                        if isinstance(parsed.get('extracted_data'), dict):
                            extracted_data = parsed['extracted_data']
                        elif isinstance(parsed.get('data'), dict):
                            extracted_data = parsed['data']
                        elif isinstance(parsed.get('result'), dict):
                            extracted_data = parsed['result']
                        else:
                            extracted_data = parsed
                    else:
                        extracted_data = {"raw": parsed}
                except Exception:
                    extracted_data = {"raw": msg.content}
                break  # Use first tool result

        return AgentChatResponse(
            response=final_response,
            extracted_data=extracted_data if extracted_data else None,
            tool_used=tool_used
        )

    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
