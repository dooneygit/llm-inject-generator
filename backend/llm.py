from typing import Literal

from pydantic import BaseModel, Field


class Inject(BaseModel):
    minute: int = Field(ge=0)
    description: str


class Scenario(BaseModel):
    title: str
    difficulty: Literal["low", "medium", "high"]
    objectives: list[str] = Field(min_length=2, max_length=4)
    injects: list[Inject] = Field(min_length=3, max_length=5)
