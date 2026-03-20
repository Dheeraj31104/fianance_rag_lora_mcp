from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.external_mcp_client import ExternalMCPClient


router = APIRouter()
external_mcp_client = ExternalMCPClient()


class ExternalMCPActionRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


@router.get("/tools")
def list_external_tools():
    return {"tools": external_mcp_client.list_tools()}


@router.post("/run")
def run_external_tool(request: ExternalMCPActionRequest):
    return {
        "tool": request.tool,
        "result": external_mcp_client.call_tool(request.tool, request.args),
    }
