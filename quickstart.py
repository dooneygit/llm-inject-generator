from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "Hi Claude! Say hi back.",
        }
    ],
)

for block in message.content:
    if block.type == "text":
        print(block.text)