from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage, ToolMessage
from app.langgraph.workflow import graph
from app.services.interaction_service import interaction_service
from app.schemas.interaction import InteractionCreate
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
        tool_message: Optional[str] = None
        tool_status: Optional[str] = None

        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_used = msg.name
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict):
                        tool_status = parsed.get('status')
                        tool_message = parsed.get('message') if isinstance(parsed.get('message'), str) else None
                        for key in ('extracted_data', 'data', 'result', 'follow_up_plan', 'insights', 'summary'):
                            if isinstance(parsed.get(key), dict):
                                extracted_data = parsed[key]
                                break
                        else:
                            extracted_data = parsed
                    else:
                        extracted_data = {"raw": parsed}
                except Exception:
                    extracted_data = {"raw": msg.content}
                break  # Use first tool result

        if (tool_status == 'error' or final_response == "I've processed your request.") and tool_message:
            final_response = tool_message

        if extracted_data and tool_used == 'log_interaction':
            payload = {
                'hcp_name': extracted_data.get('hcp_name') or extracted_data.get('doctor_name') or '',
                'hospital': extracted_data.get('hospital') or extracted_data.get('clinic') or '',
                'specialization': extracted_data.get('specialization') or extracted_data.get('specialty'),
                'interaction_date': extracted_data.get('interaction_date') or extracted_data.get('date') or '',
                'meeting_type': extracted_data.get('meeting_type') or extracted_data.get('visit_type') or 'In-person Visit',
                'visit_duration': extracted_data.get('visit_duration') or 30,
                'discussion_topics': extracted_data.get('discussion_topics') or extracted_data.get('topics'),
                'products_discussed': extracted_data.get('products_discussed') or extracted_data.get('products'),
                'objections': extracted_data.get('objections') or extracted_data.get('objection'),
                'competitor_mentioned': extracted_data.get('competitor_mentioned') or extracted_data.get('competitor'),
                'follow_up_required': bool(extracted_data.get('follow_up_required') or extracted_data.get('follow_up') or False),
                'follow_up_date': extracted_data.get('follow_up_date'),
                'notes': extracted_data.get('summary') or extracted_data.get('notes'),
                'sentiment': extracted_data.get('sentiment') or 'neutral',
                'confidence_score': extracted_data.get('confidence_score')
            }
            if payload['hcp_name'] and payload['hospital']:
                interaction_service.create_interaction(InteractionCreate(**payload))

        if extracted_data and tool_used == 'edit_interaction':
            interaction_id = extracted_data.get('interaction_id') or extracted_data.get('id')
            updated_field = extracted_data.get('updated_field') or extracted_data.get('field_to_update')
            new_value = extracted_data.get('new_value') or extracted_data.get('value')
            if interaction_id and updated_field and new_value is not None:
                interaction_service.update_interaction(str(interaction_id), {str(updated_field): new_value})

        return AgentChatResponse(
            response=final_response,
            extracted_data=extracted_data if extracted_data else None,
            tool_used=tool_used
        )

    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
