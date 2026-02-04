"""
Trend & Skill Service - Data collection layer for job market trends.

This service collects, normalizes, deduplicates, and stores:
1. Job listings from Google Jobs (via SERP API)
2. Skill discussions from Reddit (via Apify)

It does NOT perform AI analysis - that's for a separate consumer service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.routers import jobs, discussions, cron

app = FastAPI(
    title="Trend & Skill Data Collection Service",
    description="Collects job listings and skill discussions for trend analysis",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(discussions.router, prefix="/api/discussions", tags=["Discussions"])
app.include_router(cron.router, prefix="/api/cron", tags=["Cron"])


@app.get("/")
def root():
    return {
        "service": "Trend & Skill Data Collection Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "jobs": "/api/jobs",
            "discussions": "/api/discussions",
            "cron": "/api/cron"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Lambda handler
handler = Mangum(app)
