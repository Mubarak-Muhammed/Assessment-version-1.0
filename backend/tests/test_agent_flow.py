import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.endpoints.agent import agent_chat, AgentChatRequest
import asyncio


def test_agent_chat_returns_real_response():
    request = AgentChatRequest(message='I met Dr. Priya Sharma at Fortis Hospital today to discuss Cardivex 10mg')
    response = asyncio.run(agent_chat(request))
    assert response.response
    assert response.response != "I've processed your request."
    assert response.response != "The AI assistant is temporarily unavailable due to an external model quota issue. Please try again in a few minutes, or enter data manually."
