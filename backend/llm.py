import json
from typing import Literal

import anthropic
from dotenv import load_dotenv

from pydantic import BaseModel, Field

load_dotenv()

client = anthropic.Anthropic()


class Inject(BaseModel):
    minute: int = Field(ge=0)
    description: str


class Scenario(BaseModel):
    title: str
    difficulty: Literal["low", "medium", "high"]
    objectives: list[str] = Field(min_length=2, max_length=4)
    injects: list[Inject] = Field(min_length=3, max_length=5)


SYSTEM_PROMPT = f"""You are an exercise designer for emergency response training.

<constraints>
Realistic, non-graphic. 3–5 injects in chronological order.
No real people or locations.
</constraints>

<example>
{{
  "title": "Riverbend Spring Flood",
  "difficulty": "medium",
  "objectives": [
    "Coordinate evacuation of low-lying neighbourhoods",
    "Establish a unified command post with partner agencies",
    "Communicate public safety updates within 15 minutes of each change"
  ],
  "injects": [
    {{"minute": 0, "description": "River gauges show water rising 30 cm per hour after two days of heavy rain."}},
    {{"minute": 20, "description": "A care home near the river reports it cannot move 40 residents without assistance."}},
    {{"minute": 45, "description": "The main bridge out of town is closed after debris damages a support."}},
    {{"minute": 70, "description": "Social media posts falsely claim the dam upstream has failed, causing panic."}}
  ]
}}
</example>

<output_format>
Return ONLY a JSON object matching this schema: {json.dumps(Scenario.model_json_schema())}
No prose, no markdown fences.
</output_format>"""


def generate_scenario(exercise: str) -> Scenario:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": exercise},
            {"role": "assistant", "content": "{"},
        ],
    )

    print(message)
    return Scenario.model_validate_json("{" + message.content[0].text)

if __name__ == "__main__":
    print(generate_scenario("A wildfire threatening a rural town").model_dump_json(indent=2))
