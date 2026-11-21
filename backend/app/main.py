from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dashboard, stations, alerts, maintenance

app = FastAPI(
    title="Groundwater Guardian API",
    description=(
        "Groundwater monitoring data reliability "
        "and maintenance management system"
    ),
    version="1.0.0"
)

# Allow the local React/Vite frontend to access the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "project": "Groundwater Guardian"
    }


app.include_router(dashboard.router)
app.include_router(stations.router)
app.include_router(alerts.router)
app.include_router(maintenance.router)
