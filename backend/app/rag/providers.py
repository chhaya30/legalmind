from abc import ABC, abstractmethod
import json
import urllib.request
from app.core.config import settings

class LLMProvider(ABC):
    name = 'base'
    version = '1'
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...

class MockProvider(LLMProvider):
    name = 'mock-grounded'
    version = '1.0'
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Deterministic extractive fallback so Phase 3 works without an external LLM key.
        evidence = []
        in_ev = False
        for line in user_prompt.splitlines():
            line = line.strip()
            if line.startswith('EVIDENCE:'):
                in_ev = True
                continue
            if in_ev and line.startswith('[') and '] ' in line:
                citation, snippet = line.split('] ', 1)
                evidence.append((citation + ']', snippet))
        if not evidence:
            return 'I do not have enough retrieved evidence to answer this question.'
        parts = [f"The retrieved evidence indicates {snippet[:500]} {citation}" for citation, snippet in evidence[:3]]
        return ' '.join(parts)

class OpenAICompatibleProvider(LLMProvider):
    name = 'openai-compatible'
    version = '1.0'
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key, self.model, self.base_url = api_key, model, base_url.rstrip('/')
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps({'model': self.model, 'messages': [
            {'role':'system','content':system_prompt}, {'role':'user','content':user_prompt}
        ], 'temperature': 0.1}).encode()
        req = urllib.request.Request(self.base_url + '/chat/completions', data=payload, headers={
            'Content-Type':'application/json', 'Authorization':f'Bearer {self.api_key}'})
        with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode())
        return data['choices'][0]['message']['content']

def get_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == 'openai-compatible' and settings.LLM_API_KEY:
        return OpenAICompatibleProvider(settings.LLM_API_KEY, settings.LLM_MODEL, settings.LLM_BASE_URL)
    return MockProvider()
