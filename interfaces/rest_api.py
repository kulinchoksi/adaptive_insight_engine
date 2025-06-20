import os
import uuid
import traceback
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.runners import InMemorySessionService
from google.genai.types import Blob, Content, Part

from adaptive_insight_engine.agent import root_agent
from utils.logger import configure_logging
import structlog

# For remote agent access
try:
    from vertexai import agent_engines
except ImportError:
    agent_engines = None

import os
from dotenv import load_dotenv
load_dotenv()
RESOURCE_ID = os.getenv("RESOURCE_ID")
AGENT_BACKEND = os.getenv("AGENT_BACKEND", "local").lower()

def get_agent_runner():
    if AGENT_BACKEND == "vertexai" and RESOURCE_ID and agent_engines is not None:
        return agent_engines.get(RESOURCE_ID)
    else:
        session_service = InMemorySessionService()
        return Runner(agent=root_agent, app_name="AIE", session_service=session_service)

# Configure logging
configure_logging()
log = structlog.get_logger()

runner = get_agent_runner()

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
    trace_id = str(uuid.uuid4())
    log.info(
        "/analyze endpoint called",
        feature_toggle=feature_toggle,
        narrative_toggle=narrative_toggle,
        followup_query=followup_query,
        trace_id=trace_id,
    )

    parts = []
    # Add text parts for toggles and query
    parts.append(Part.from_text(text=f"Feature Toggle: {feature_toggle}"))
    parts.append(Part.from_text(text=f"Narrative Toggle: {narrative_toggle}"))
    if followup_query:
        parts.append(Part.from_text(text=f"Follow-up Query: {followup_query}"))

    # Add file part
    if file and file.filename:
        file_content = await file.read()
        mime_type = file.content_type
        file_blob = Blob(data=file_content, mime_type=mime_type)
        parts.append(Part(inline_data=file_blob))

    content = Content(parts=parts)
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Explicitly create the session to avoid "Session not found" error (local only)
    try:
        if hasattr(runner, "session_service"):
            await runner.session_service.create_session(session_id=session_id, user_id=user_id, app_name="AIE")
    except ValueError:
        # This should not happen with UUIDs, but handle defensively
        log.warning(
            "Attempted to create a session that already exists.",
            session_id=session_id,
            trace_id=trace_id,
        )
        pass

    final_response_text = ""
    try:
        if hasattr(runner, "run_async"):
            # Local agent: stream responses
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                    log.info(
                        "Agent returned final response.",
                        response=final_response_text,
                        trace_id=trace_id,
                    )
                    break
        else:
            # Remote agent: use .query(input=...)
            input_str = ""
            for part in parts:
                if hasattr(part, "text") and part.text is not None:
                    input_str += part.text + "\n"
            from utils.vertex_agent_rest import call_vertex_agent_rest
            result = call_vertex_agent_rest(input_str)
            log.info(
                "Agent returned final response.",
                response=result,
                trace_id=trace_id,
            )

            if isinstance(result, dict):
                if 'error' in result:
                    return AnalysisResponse(
                        status="error",
                        message=result['error'],
                    )
                elif 'tool_calls' in result:
                    return AnalysisResponse(
                        status="success",
                        result={"tool_calls": result['tool_calls']},
                        message="Analysis complete.",
                    )
                else:
                    return AnalysisResponse(
                        status="success",
                        result={"analysis": result.get('text', '')},
                        message="Analysis complete.",
                    )
            else:
                return AnalysisResponse(
                    status="success",
                    result={"analysis": result},
                    message="Analysis complete.",
                )

        if not final_response_text:
            log.warning("Agent did not return a final response.", trace_id=trace_id)
            return JSONResponse(
                status_code=500,
                content=AnalysisResponse(
                    status="error", message="Agent did not produce a final response."
                ).model_dump(),
            )

        return AnalysisResponse(
            status="success",
            result={"analysis": final_response_text},
            message="Analysis complete.",
        )
    except Exception as e:
        log.error(
            "An error occurred during agent execution.",
            error=str(e),
            trace_id=trace_id,
            exception=traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content=AnalysisResponse(
                status="error", message=f"An internal error occurred: {str(e)}"
            ).model_dump(),
        )


@app.get("/")
def root():
    return {"message": "Adaptive Insight Engine API is running."}