import requests

url = 'http://127.0.0.1:8000/agent/chat'
payload = {'message': 'I met Dr. Priya Sharma at Fortis Hospital today to discuss Cardivex 10mg', 'context': {}}
response = requests.post(url, json=payload)
print('status', response.status_code)
print('body', response.text)
