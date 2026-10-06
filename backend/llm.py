from typing import Literal

import anthropic
from dotenv import load_dotenv
from fastapi import HTTPException

from pydantic import BaseModel, Field, ValidationError

load_dotenv()

client = anthropic.Anthropic(timeout=30.0, max_retries=2)


class Inject(BaseModel):
    minute: int = Field(ge=0)
    description: str


class Scenario(BaseModel):
    title: str
    difficulty: Literal["low", "medium", "high"]
    objectives: list[str] = Field(min_length=2, max_length=4)
    injects: list[Inject] = Field(min_length=3, max_length=5)


SYSTEM_PROMPT = """You are an exercise designer for emergency response training.

<constraints>
Realistic, non-graphic. 3–5 injects in chronological order.
No real people or locations.
</constraints>

<example>
{
  "title": "Riverbend Spring Flood",
  "difficulty": "medium",
  "objectives": [
    "Coordinate evacuation of low-lying neighbourhoods",
    "Establish a unified command post with partner agencies",
    "Communicate public safety updates within 15 minutes of each change"
  ],
  "injects": [
    {"minute": 0, "description": "River gauges show water rising 30 cm per hour after two days of heavy rain."},
    {"minute": 20, "description": "A care home near the river reports it cannot move 40 residents without assistance."},
    {"minute": 45, "description": "The main bridge out of town is closed after debris damages a support."},
    {"minute": 70, "description": "Social media posts falsely claim the dam upstream has failed, causing panic."}
  ]
}
</example>
"""


def generate_scenario(exercise: str) -> Scenario:
    try:
        message = client.messages.parse(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": exercise}],
            output_format=Scenario,
        )
    except anthropic.APITimeoutError:
        raise HTTPException(504, "Scenario generation timed out")
    except anthropic.RateLimitError:
        raise HTTPException(503, "Scenario service is busy, try again later")
    except anthropic.BadRequestError:
        raise HTTPException(400, "Exercise description could not be processed")
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        raise HTTPException(502, "Upstream LLM service error")
    except ValidationError:
        raise HTTPException(502, "LLM returned an invalid scenario")

    if message.stop_reason == "refusal":
        raise HTTPException(422, "Exercise description was refused")
    if message.stop_reason == "max_tokens" or message.parsed_output is None:
        raise HTTPException(502, "LLM returned an incomplete scenario")

    return message.parsed_output


if __name__ == "__main__":
    print(generate_scenario("A wildfire threatening a rural town").model_dump_json(indent=2))
