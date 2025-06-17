from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from utils.logger import configure_logging
import structlog
from agents.agent import root_agent
import os

# Placeholder for agent import
# from agents.user_interaction_agent import UserInteractionAgent

configure_logging()
logger = structlog.get_logger("FastAPI")

app = FastAPI(title="Adaptive Insight Engine API")

class AnalysisRequest(BaseModel):
    feature_toggle: bool = False
    narrative_toggle: bool = False
    followup_query: Optional[str] = None

class AnalysisResponse(BaseModel):
    status: str
    result: Optional[dict] = None
    message: Optional[str] = None

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    feature_toggle: bool = Form(False),
    narrative_toggle: bool = Form(False),
    followup_query: Optional[str] = Form(None),
):
    logger.info("/analyze endpoint called", feature_toggle=feature_toggle, narrative_toggle=narrative_toggle, followup_query=followup_query)
    file_type = os.path.splitext(file.filename)[-1].replace(".", "").lower() if file else None
    input_data = {
        "file": file,
        "file_type": file_type,
        "feature_toggle": feature_toggle,
        "narrative_toggle": narrative_toggle,
        "followup_query": followup_query,
    }
    result = await root_agent.run_async(input_data=input_data)
    return AnalysisResponse(
        status="success",
        result=result,
        message="Analysis complete."
    )

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Adaptive Insight Engine API is running."} 