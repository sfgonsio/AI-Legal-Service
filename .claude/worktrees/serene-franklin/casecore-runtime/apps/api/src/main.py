from fastapi import FastAPI
from src.config import settings
from src.routers import cases, intake, evidence, artifacts, reviews, workflow, audit, retrieval

app = FastAPI(title=settings.app_name)

app.include_router(cases.router, prefix=settings.api_prefix)
app.include_router(intake.router, prefix=settings.api_prefix)
app.include_router(evidence.router, prefix=settings.api_prefix)
app.include_router(artifacts.router, prefix=settings.api_prefix)
app.include_router(reviews.router, prefix=settings.api_prefix)
app.include_router(workflow.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(retrieval.router, prefix=settings.api_prefix)

