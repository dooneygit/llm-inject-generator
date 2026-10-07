import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Query, status
from pydantic import BaseModel, StringConstraints

from llm import Scenario, generate_scenario
from llm_errors import LLMError, llm_error_handler

DB_PATH = Path(__file__).parent / "scenarios.db"


def get_db():
    # check_same_thread=False: FastAPI may run the dependency and the endpoint
    # on different threadpool threads. The connection is never shared across requests.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    scenario_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
    finally:
        conn.close()
    yield


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(LLMError, llm_error_handler)

Db = Annotated[sqlite3.Connection, Depends(get_db)]


class ScenarioCreate(BaseModel):
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


class ScenarioRecord(BaseModel):
    id: int
    description: str
    scenario: Scenario
    created_at: datetime


def to_record(row: sqlite3.Row) -> ScenarioRecord:
    return ScenarioRecord(
        id=row["id"],
        description=row["description"],
        scenario=Scenario.model_validate_json(row["scenario_json"]),
        created_at=row["created_at"],
    )


@app.post("/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(body: ScenarioCreate, db: Db) -> ScenarioRecord:
    scenario = generate_scenario(body.description)
    created_at = datetime.now(timezone.utc).isoformat()
    with db:
        cur = db.execute(
            "INSERT INTO scenarios (description, scenario_json, created_at) VALUES (?, ?, ?)",
            (body.description, scenario.model_dump_json(), created_at),
        )
    return ScenarioRecord(
        id=cur.lastrowid,
        description=body.description,
        scenario=scenario,
        created_at=created_at,
    )


@app.get("/scenarios")
def list_scenarios(
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ScenarioRecord]:
    rows = db.execute(
        "SELECT id, description, scenario_json, created_at FROM scenarios"
        " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [to_record(row) for row in rows]
