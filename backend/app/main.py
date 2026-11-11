from fastapi import FastAPI

from app.routers import dashboard, stations, alerts, maintenance

app = FastAPI(
    title="Groundwater Guardian API",
    description=(
        "Groundwater monitoring data reliability "
        "and maintenance management system"
    ),
    version="1.0.0"
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
