from app.core.config import settings
import groq

print('GROQ key available:', bool(settings.GROQ_API_KEY))
print('Configured model:', settings.MODEL_NAME)
client = groq.Groq(api_key=settings.GROQ_API_KEY)
models = client.models.list().data
print('Total available models:', len(models))
for m in models:
    if m.id in {'groq/compound-mini', 'groq/compound', 'llama-3.1-8b-instant', 'openai/gpt-oss-20b', 'llama-3.3-70b-versatile'}:
        print('---')
        print('id:', m.id)
        print('active:', m.active)
        print('supported_features:', getattr(m, 'supported_features', None))
        print('input_modalities:', getattr(m, 'input_modalities', None))
        print('output_modalities:', getattr(m, 'output_modalities', None))
        print('max_completion_tokens:', getattr(m, 'max_completion_tokens', None))
        print('pricing:', getattr(m, 'pricing', None))
        print('name:', getattr(m, 'name', None))
