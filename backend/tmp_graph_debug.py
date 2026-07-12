import traceback
from app.langgraph.workflow import graph
from langchain_core.messages import HumanMessage

state = {
    'messages': [HumanMessage(content='I met Dr. Priya Sharma at Fortis Hospital today to discuss Cardivex 10mg')],
    'extracted_data': {}
}

try:
    res = graph.invoke(state)
    print('RESULT:', res)
    print('MESSAGES:', type(res.get('messages')) if hasattr(res, 'get') else type(res))
    for msg in res.get('messages', []):
        print('MSG TYPE', type(msg).__name__)
        print('  name=', getattr(msg, 'name', None))
        print('  content=', getattr(msg, 'content', None))
        print('  tool_calls=', getattr(msg, 'tool_calls', None))
except Exception as exc:
    print('EXCEPTION:', type(exc).__name__, exc)
    traceback.print_exc()
