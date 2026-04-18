import anthropic
import httpx
import os

print(f"API key present: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
print(f"API key prefix: {os.environ.get('ANTHROPIC_API_KEY', '')[:8]}...")

http_client = httpx.Client(headers={"User-Agent": "salasblog2/1.0"})
client = anthropic.Anthropic(
    http_client=http_client,
    default_headers={"User-Agent": "salasblog2/1.0"},
)

message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=50,
    messages=[{"role": "user", "content": "hello"}],
)
print(f"Success! Response: {message.content[0].text!r}")
