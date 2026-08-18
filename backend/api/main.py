from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.api.routes import categories, companies, internships

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Business Internship Aggregator API",
    description="Read-only API over business-relevant internship listings collected from company career sites.",
    version="0.1.0",
)

# Comma-separated list, e.g. "http://localhost:3000,https://myapp.example.com".
# Defaults to the standard local Next.js dev server origin.
_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    # Never leak SQL, connection strings, or stack traces to API consumers.
    logger.exception("Database error handling %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."})


app.include_router(internships.router)
app.include_router(companies.router)
app.include_router(categories.router)


@app.get("/", tags=["health"], summary="Health check")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "business-internship-aggregator-api"}
