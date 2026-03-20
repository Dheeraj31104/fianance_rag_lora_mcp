from app.services.mcp_service import MCPService


def build_tool_registry() -> dict:
    return MCPService().get_tools()
