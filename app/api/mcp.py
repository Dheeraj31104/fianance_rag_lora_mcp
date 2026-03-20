from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.mcp_service import MCPService


router = APIRouter()
mcp_service = MCPService()


class MCPActionRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


@router.get("/tools")
def list_tools():
    return {"tools": sorted(mcp_service.get_tools().keys())}


@router.post("/run")
def run_tool(request: MCPActionRequest):
    tools = mcp_service.get_tools()
    tool = tools.get(request.tool)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.tool}")
    return {"tool": request.tool, "result": tool(**request.args)}
