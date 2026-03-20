from fastapi import FastAPI

from routes.health import router as health_router
from routes.runs import router as runs_router
from routes.artifacts import router as artifacts_router
from routes.promotion import router as promotion_router
from routes.audit import router as audit_router

app = FastAPI(title="CASECORE Runtime API", version="0.1.0")

app.include_router(health_router)
app.include_router(runs_router)
app.include_router(artifacts_router)
app.include_router(promotion_router)
app.include_router(audit_router)
