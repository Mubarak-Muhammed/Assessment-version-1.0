from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class InteractionBase(BaseModel):
    hcp_name: str
    hospital: str
    specialization: Optional[str] = None
    interaction_date: Optional[str] = None
    meeting_type: str
    visit_duration: Optional[int] = None
    discussion_topics: Optional[str] = None
    products_discussed: Optional[str] = None
    objections: Optional[str] = None
    competitor_mentioned: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    sentiment: Optional[str] = None
    confidence_score: Optional[float] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(InteractionBase):
    pass

class InteractionInDB(InteractionBase):
    id: str

    class Config:
        orm_mode = True
        from_attributes = True

class AgentChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentChatResponse(BaseModel):
    response: str
    extracted_data: Optional[Dict[str, Any]] = None

