from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class CommandInfo(BaseModel):
    name: str
    description: Optional[str] = None
    args_schema: Optional[Dict[str, Any]] = None


class ExecuteRequest(BaseModel):
    command: str
    args: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExecuteResponse(BaseModel):
    ok: bool
    output: Optional[str] = None
    data: Optional[Any] = None
    logs: Optional[List[str]] = None
    error: Optional[str] = None
