from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, commentary, external_mcp, mcp, portfolio, qa, risk, stocks


app = FastAPI(title="Finance Analytics Platform", version="0.1.0")
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(risk.router, prefix="/risk", tags=["risk"])
app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
app.include_router(commentary.router, prefix="/commentary", tags=["commentary"])
app.include_router(qa.router, prefix="/qa", tags=["qa"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
app.include_router(external_mcp.router, prefix="/external-mcp", tags=["external-mcp"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")
