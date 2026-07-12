# TODO: Replace mock storage with SQLAlchemy implementation.
from sqlalchemy import Column, Integer, String, Date, Boolean, Float
from app.database.session import Base

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(String, primary_key=True, index=True)
    hcp_name = Column(String, index=True)
    hospital = Column(String)
    specialization = Column(String)
    interaction_date = Column(String) # Keeping as String for simplicity since Pydantic schema uses string datetime
    meeting_type = Column(String)
    visit_duration = Column(Integer)
    discussion_topics = Column(String)
    products_discussed = Column(String)
    objections = Column(String)
    competitor_mentioned = Column(String)
    follow_up_required = Column(Boolean)
    follow_up_date = Column(String)
    notes = Column(String)
    sentiment = Column(String)
    confidence_score = Column(Float)
