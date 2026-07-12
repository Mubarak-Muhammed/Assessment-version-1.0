import asyncio
import json
import logging
import re
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, ToolMessage

from app.langgraph.workflow import graph
from app.services.interaction_service import interaction_service
from app.schemas.interaction import InteractionCreate
from app.tools.crm_tools import (
    log_interaction,
    edit_interaction,
    generate_follow_up_plan,
    doctor_insights,
    meeting_summary_generator,
)

logger = logging.getLogger(__name__)
router = APIRouter()

class AgentChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentChatResponse(BaseModel):
    response: str
    extracted_data: Optional[Dict[str, Any]] = None
    tool_used: Optional[str] = None


def _build_log_payload(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'hcp_name': extracted_data.get('hcp_name') or extracted_data.get('doctor_name') or '',
        'hospital': extracted_data.get('hospital') or extracted_data.get('clinic') or '',
        'specialization': extracted_data.get('specialization') or extracted_data.get('specialty'),
        'interaction_date': extracted_data.get('interaction_date') or extracted_data.get('date') or '',
        'meeting_type': extracted_data.get('meeting_type') or extracted_data.get('visit_type') or 'In-person Visit',
        'visit_duration': extracted_data.get('visit_duration') or extracted_data.get('duration') or 30,
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


def _persist_interaction_result(tool_name: Optional[str], extracted_data: Optional[Dict[str, Any]]):
    if not tool_name or not extracted_data:
        return None

    if tool_name == 'log_interaction':
        payload = _build_log_payload(extracted_data)
        if payload['hcp_name'] or payload['hospital'] or payload['notes']:
            try:
                return interaction_service.create_interaction(InteractionCreate(**payload))
            except Exception:
                logger.exception("Failed to create interaction from chat tool")
        return None

    if tool_name == 'edit_interaction':
        interaction_id = extracted_data.get('interaction_id') or extracted_data.get('id')
        updated_field = extracted_data.get('updated_field') or extracted_data.get('field_to_update')
        new_value = extracted_data.get('new_value') or extracted_data.get('value')
        target_id = None

        if interaction_id and str(interaction_id).lower() not in {'unknown', 'none', 'null'}:
            target_id = str(interaction_id)
        elif interaction_id is None:
            existing = interaction_service.get_all_interactions()
            if existing:
                target_id = existing[-1].id

        if target_id and updated_field and new_value is not None:
            try:
                existing = interaction_service.get_interaction(target_id)
                if existing is None:
                    existing_items = interaction_service.get_all_interactions()
                    if existing_items:
                        target_id = existing_items[-1].id
                return interaction_service.update_interaction(str(target_id), {str(updated_field): new_value})
            except Exception:
                logger.exception("Failed to update interaction from chat tool")
        return None

    return None


def _dispatch_direct_tool(message: str):
    normalized = message.lower()
    if re.search(r"\b(edit|update|change)\b", normalized) and "interaction" in normalized:
        interaction_id_match = re.search(r"interaction\s+([a-z0-9_-]+)", message, re.I)
        interaction_id = interaction_id_match.group(1) if interaction_id_match else "unknown"
        field_match = re.search(r"\b(set|update|change)\s+([a-z_]+)\s+to\b", message, re.I)
        field_to_update = field_match.group(2) if field_match else "notes"
        value_match = re.search(r"\bto\s+(.+)$", message, re.I)
        new_value = value_match.group(1).strip().rstrip('.') if value_match else "updated"
        tool_output = edit_interaction.func(interaction_id, field_to_update, new_value) if hasattr(edit_interaction, "func") else edit_interaction(interaction_id, field_to_update, new_value)
        return "edit_interaction", tool_output

    if re.search(r"\bfollow[- ]up\b", normalized) or "next step" in normalized or "next steps" in normalized:
        tool_output = generate_follow_up_plan.func(message) if hasattr(generate_follow_up_plan, "func") else generate_follow_up_plan(message)
        return "generate_follow_up_plan", tool_output

    if "insight" in normalized or ("doctor" in normalized and "specialty" in normalized):
        tool_output = doctor_insights.func(message) if hasattr(doctor_insights, "func") else doctor_insights(message)
        return "doctor_insights", tool_output

    if "summarize" in normalized or "summary" in normalized or "meeting notes" in normalized:
        tool_output = meeting_summary_generator.func(message) if hasattr(meeting_summary_generator, "func") else meeting_summary_generator(message)
        return "meeting_summary_generator", tool_output

    tool_output = log_interaction.func(message) if hasattr(log_interaction, "func") else log_interaction(message)
    return "log_interaction", tool_output


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(data: AgentChatRequest):
    try:
        logger.info("Received agent chat request")
        logger.debug("Request payload: %s", data)

        tool_name, tool_output = _dispatch_direct_tool(data.message)
        if tool_name in {"edit_interaction", "generate_follow_up_plan", "doctor_insights", "meeting_summary_generator", "log_interaction"}:
            logger.info("Using direct tool dispatch for %s", tool_name)
            parsed = None
            try:
                parsed = json.loads(tool_output)
            except Exception:
                parsed = None

            extracted_data = {}
            tool_message = None
            tool_status = None

            if isinstance(parsed, dict):
                tool_status = parsed.get('status') if isinstance(parsed.get('status'), str) else None
                tool_message = parsed.get('message') if isinstance(parsed.get('message'), str) else None
                for key in ('extracted_data', 'data', 'result', 'follow_up_plan', 'insights', 'summary'):
                    if isinstance(parsed.get(key), dict):
                        extracted_data = parsed[key]
                        break
                if not extracted_data and any(key in parsed for key in ('extracted_data', 'data', 'result', 'follow_up_plan', 'insights', 'summary')):
                    extracted_data = parsed
                elif not extracted_data:
                    extracted_data = parsed

            final_response = tool_message or "Action completed."
            if tool_name == 'edit_interaction':
                final_response = tool_message or f"Interaction update requested for {data.message}."
            elif tool_name == 'generate_follow_up_plan':
                final_response = tool_message or "Follow-up plan generated."
            elif tool_name == 'doctor_insights':
                final_response = tool_message or "Doctor insights generated."
            elif tool_name == 'meeting_summary_generator':
                final_response = tool_message or "Meeting summary generated."
            else:
                final_response = tool_message or "Interaction logged successfully."

            _persist_interaction_result(tool_name, extracted_data)

            return AgentChatResponse(
                response=final_response,
                extracted_data=extracted_data if extracted_data else None,
                tool_used=tool_name,
            )

        initial_state = {
            "messages": [HumanMessage(content=data.message)],
            "extracted_data": {}
        }

        try:
            result = await asyncio.wait_for(asyncio.to_thread(graph.invoke, initial_state), timeout=15)
        except asyncio.TimeoutError:
            logger.warning("Graph invocation timed out")
            raise HTTPException(status_code=504, detail="The AI service is responding too slowly. Please try again in a moment or use manual entry.")

        logger.debug("Graph invocation result: %s", result)
        messages = result.get("messages", [])
        logger.debug("Result messages count=%d", len(messages))

        # Extract the final AI text response (last non-tool message)
        final_response = "I've processed your request."
        for msg in reversed(messages):
            msg_type = type(msg).__name__
            if msg_type in ("AIMessage", "SystemMessage"):
                content = getattr(msg, "content", None)
                if isinstance(content, str) and content.strip():
                    final_response = content.strip()
                    break
                elif isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    combined = " ".join(text_parts).strip()
                    if combined:
                        final_response = combined
                        break

        def _extract_json_from_string(content: str) -> Optional[Dict[str, Any]]:
            if not isinstance(content, str):
                return None
            try:
                return json.loads(content)
            except Exception:
                pass

            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end > start:
                candidate = content[start:end+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
            return None

        def format_tool_text(tool_name: Optional[str], data: Dict[str, Any], fallback_message: Optional[str]) -> str:
            if fallback_message:
                return fallback_message

            if not data:
                return ''

            if tool_name == 'log_interaction':
                if isinstance(data.get('summary'), str) and data['summary'].strip():
                    return data['summary']
                return 'Structured CRM data has been extracted successfully.'

            if tool_name == 'generate_follow_up_plan':
                if isinstance(data.get('agenda'), list):
                    agenda = ', '.join(map(str, data['agenda']))
                    return f"Follow-up plan created. Agenda: {agenda}."
                if isinstance(data.get('reminder_note'), str):
                    return f"Follow-up plan created. {data['reminder_note']}"
                return 'A follow-up plan has been generated.'

            if tool_name == 'doctor_insights':
                if isinstance(data.get('engagement_strategy'), str):
                    return f"Doctor insights generated. Strategy: {data['engagement_strategy']}"
                return 'Doctor insights have been generated.'

            if tool_name == 'meeting_summary_generator':
                if isinstance(data.get('executive_summary'), str):
                    return data['executive_summary']
                return 'Meeting summary has been generated.'

            if isinstance(data.get('summary'), str):
                return data['summary']
            if isinstance(data.get('message'), str):
                return data['message']
            return json.dumps(data, ensure_ascii=False)

        def extract_tool_content(msg: ToolMessage):
            try:
                parsed = json.loads(msg.content)
            except Exception:
                parsed = None

            extracted = {}
            tool_msg = None
            status = None

            if isinstance(parsed, dict):
                status = parsed.get('status') if isinstance(parsed.get('status'), str) else None
                tool_msg = parsed.get('message') if isinstance(parsed.get('message'), str) else None
                for key in ('extracted_data', 'data', 'result', 'follow_up_plan', 'insights', 'summary'):
                    if isinstance(parsed.get(key), dict):
                        extracted = parsed[key]
                        break
                if not extracted and any(key in parsed for key in ('extracted_data', 'data', 'result', 'follow_up_plan', 'insights', 'summary')):
                    extracted = parsed
            elif isinstance(msg.content, str):
                tool_msg = msg.content
                extracted = {"raw": msg.content}

            return msg.name, extracted, tool_msg, status

        extracted_data: Dict[str, Any] = {}
        tool_used: Optional[str] = None
        tool_message: Optional[str] = None
        tool_status: Optional[str] = None

        for msg in messages:
            if isinstance(msg, ToolMessage):
                logger.debug("Processing tool message: name=%s content=%s", msg.name, getattr(msg, 'content', None))
                name, extracted, msg_text, status = extract_tool_content(msg)
                logger.debug("Extracted tool payload: name=%s status=%s message=%s extracted=%s", name, status, msg_text, extracted)
                tool_used = name or tool_used
                tool_status = status or tool_status
                if msg_text and not tool_message:
                    tool_message = msg_text
                if extracted and not extracted_data:
                    extracted_data = extracted
                if tool_message and extracted_data:
                    break

        tool_output = format_tool_text(tool_used, extracted_data, tool_message)
        logger.debug("Final extracted values: final_response=%s tool_used=%s tool_status=%s tool_message=%s extracted_data=%s", final_response, tool_used, tool_status, tool_message, extracted_data)

        if ((final_response == "I've processed your request." or not final_response.strip() or final_response == 'No response' or tool_status == 'error') and tool_output):
            logger.info("Replacing placeholder response with tool output")
            final_response = tool_output

        if final_response == "I've processed your request." and extracted_data:
            logger.info("Placeholder response with extracted data present, using tool_output")
            final_response = tool_output or "Structured CRM data has been extracted successfully."

        _persist_interaction_result(tool_used, extracted_data)

        return AgentChatResponse(
            response=final_response,
            extracted_data=extracted_data if extracted_data else None,
            tool_used=tool_used
        )

    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
