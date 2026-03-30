"""FastAPI app stub for channel endpoints and health checks."""

from fastapi import FastAPI

app = FastAPI(title="Customer Success FTE API")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# TODO: Add webhook endpoints for Gmail and WhatsApp, and include web form router
