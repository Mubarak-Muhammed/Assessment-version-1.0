from langchain_core.tools import tool
from typing import Optional
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Lazy-load LLM inside each tool to avoid circular imports
def _get_llm():
    from app.core.config import settings
    return ChatGroq(
        temperature=0,
        model_name=settings.MODEL_NAME,
        api_key=settings.GROQ_API_KEY,
    )

def _extract_json(content: str) -> dict:
    """Try to extract JSON from LLM response."""
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {"raw_response": content}


# ── Tool 1: Log Interaction ──────────────────────────────────────────────────
@tool
def log_interaction(conversation_text: str) -> str:
    """
    Analyzes field rep notes about a meeting with an HCP (Healthcare Professional).
    Uses AI to extract structured CRM data including HCP name, hospital, products
    discussed, objections raised, sentiment, and whether follow-up is required.
    Returns a structured JSON summary ready to be stored in the CRM.
    """
    llm = _get_llm()
    prompt = f"""You are a life sciences CRM AI assistant. A field representative has shared notes from an HCP visit.
Extract structured CRM data from the notes below.

Return ONLY a valid JSON object with these exact keys:
- hcp_name (string): Doctor's full name
- hospital (string): Hospital or clinic name
- specialization (string): Medical specialty (e.g. Cardiology, Oncology)
- meeting_type (string): Type of visit (e.g. In-person, Virtual, Conference)
- visit_duration (number): How many minutes the meeting lasted
- discussion_topics (string): Main topics covered in the meeting
- products_discussed (string): Drug/product names mentioned
- objections (string): Any concerns or objections raised by the HCP
- competitor_mentioned (string): Any competitor products mentioned
- follow_up_required (boolean): true if follow-up is needed
- follow_up_date (string): Recommended follow-up date in ISO format if available
- notes (string): Any additional notes or observations
- sentiment (string): "positive", "neutral", or "negative"
- confidence_score (number): 0.0 to 1.0 confidence in the extraction
- summary (string): 2-sentence professional summary of the meeting

If a value cannot be extracted, return an empty string for text fields, false for boolean fields, and 0.0 for numerical fields.

Field Rep Notes:
{conversation_text}

Return ONLY the JSON object, no markdown, no explanation."""

    response = llm.invoke([HumanMessage(content=prompt)])
    extracted = _extract_json(response.content)
    return json.dumps({
        "status": "success",
        "message": "Interaction successfully analyzed and structured for CRM entry.",
        "extracted_data": extracted
    })


# ── Tool 2: Edit Interaction ─────────────────────────────────────────────────
@tool
def edit_interaction(interaction_id: str, field_to_update: str, new_value: str) -> str:
    """
    Edits a specific field of an already-logged HCP interaction in the CRM.
    Provide the interaction ID, the field name to change (e.g. 'notes',
    'follow_up_date', 'products_discussed', 'sentiment'), and the new value.
    Use this when a rep wants to correct or update a logged interaction.
    """
    # In production: calls interaction_repo.update(interaction_id, {field_to_update: new_value})
    allowed_fields = [
        "hcp_name", "hospital", "specialization", "meeting_type",
        "products_discussed", "objections", "competitor_mentioned",
        "follow_up_required", "follow_up_date", "notes", "sentiment",
        "confidence_score", "discussion_topics", "visit_duration"
    ]

    if field_to_update not in allowed_fields:
        return json.dumps({
            "status": "error",
            "message": f"Field '{field_to_update}' is not editable. Allowed fields: {', '.join(allowed_fields)}"
        })

    return json.dumps({
        "status": "success",
        "interaction_id": interaction_id,
        "updated_field": field_to_update,
        "new_value": new_value,
        "message": f"✅ Interaction {interaction_id[:8]}... updated: '{field_to_update}' changed to '{new_value}'"
    })


# ── Tool 3: Generate Follow-Up Plan ─────────────────────────────────────────
@tool
def generate_follow_up_plan(interaction_summary: str | dict) -> str:
    """
    Generates an AI-powered follow-up plan for a field rep based on an HCP
    interaction summary. Returns recommended next visit date, visit agenda,
    priority level, key talking points, and reminder notes.
    Use this after logging a meeting to plan the next steps.
    """
    llm = _get_llm()
    if isinstance(interaction_summary, dict):
        interaction_summary = json.dumps(interaction_summary)
        
    prompt = f"""You are a life sciences sales coach. A field rep just had an HCP meeting.
Based on the interaction summary below, generate a strategic follow-up plan.

Interaction Summary:
{interaction_summary}

Return ONLY a valid JSON object with:
- next_visit_days (integer): Recommended days from today for next visit
- priority (string): "High", "Medium", or "Low"
- agenda (array of 3 strings): Topics to cover in next meeting
- talking_points (array of 2 strings): Key messages to reinforce
- reminder_note (string): Important reminder for the rep
- recommended_materials (array of 2 strings): Brochures or samples to bring
- follow_up_email_subject (string): Suggested email subject line

Return ONLY the JSON, no markdown."""

    response = llm.invoke([HumanMessage(content=prompt)])
    result = _extract_json(response.content)
    return json.dumps({
        "status": "success",
        "message": "Follow-up plan generated successfully.",
        "follow_up_plan": result
    })


# ── Tool 4: Doctor Insights ──────────────────────────────────────────────────
@tool
def doctor_insights(doctor_name: str, specialty: Optional[str] = None) -> str:
    """
    Generates a comprehensive HCP profile and strategic insights for a given doctor.
    Returns buying interest level, preferred product categories, communication style,
    best visit times, key concerns, and recommended engagement strategy.
    Use this before visiting a doctor to prepare the rep.
    """
    llm = _get_llm()
    spec_context = f"Specialty: {specialty}" if specialty else "Specialty: Unknown"
    prompt = f"""You are a life sciences CRM AI. Generate a realistic and detailed HCP profile for sales planning.

Doctor: {doctor_name}
{spec_context}

Return ONLY a valid JSON object with:
- buying_interest (string): "High", "Medium", or "Low"
- prescribing_behavior (string): Description of prescribing patterns
- preferred_topics (array of 3 strings): Topics this doctor responds well to
- communication_style (string): e.g. "Data-driven and analytical"
- best_visit_time (string): e.g. "Tuesday mornings, 9-11 AM"
- key_concerns (array of 2 strings): Doctor's main concerns about products
- engagement_strategy (string): How to best engage this HCP
- influence_score (integer 1-10): Overall influence in their network
- relationship_tier (string): "Key Opinion Leader", "Regular Prescriber", or "New Contact"

Return ONLY the JSON, no markdown."""

    response = llm.invoke([HumanMessage(content=prompt)])
    result = _extract_json(response.content)
    return json.dumps({
        "status": "success",
        "doctor": doctor_name,
        "insights": result
    })


# ── Tool 5: Meeting Summary Generator ───────────────────────────────────────
@tool
def meeting_summary_generator(raw_notes: str) -> str:
    """
    Converts long, unstructured field rep meeting notes into a professional,
    concise CRM summary with key takeaways, agreed action items, next steps,
    and overall meeting outcome. Use this to clean up raw notes for reporting.
    """
    llm = _get_llm()
    prompt = f"""You are a professional CRM documentation assistant for a life sciences company.
Transform these raw field rep notes into a polished CRM entry.

Raw Notes:
{raw_notes}

Return ONLY a valid JSON object with:
- executive_summary (string): 2-sentence professional summary
- key_takeaways (array of 3 strings): Most important points from the meeting
- action_items (array of objects with 'task', 'owner', 'deadline'): Agreed actions
- next_steps (string): What happens next
- overall_outcome (string): "Positive", "Neutral", or "Needs Follow-up"
- meeting_effectiveness_score (integer 1-10): How productive the meeting was
- notes_for_manager (string): Brief note for the sales manager

Return ONLY the JSON, no markdown."""

    response = llm.invoke([HumanMessage(content=prompt)])
    result = _extract_json(response.content)
    return json.dumps({
        "status": "success",
        "message": "Meeting notes successfully summarized.",
        "summary": result
    })
