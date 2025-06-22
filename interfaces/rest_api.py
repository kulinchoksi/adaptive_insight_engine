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

from adaptive_insight_engine.agent import workflow_orchestrator_agent
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
        return Runner(agent=workflow_orchestrator_agent, app_name="AIE", session_service=session_service)

# Configure logging
configure_logging()
log = structlog.get_logger()

runner = get_agent_runner()

app = FastAPI(title="Adaptive Insight Engine API")


from fastapi import Body

class AnalyzeResponse(BaseModel):
    status: str
    session_id: str
    result: Optional[dict] = None
    message: Optional[str] = None

@app.post("/analyze", response_model=AnalyzeResponse, summary="Conversational analysis endpoint", description="""
Submit a file and/or a text query for analysis. Use the same session_id for follow-up queries to maintain context. If session_id is omitted, a new analysis session is started. You must provide at least a file or a text query.

- To start a new analysis: omit session_id or provide a new one.
- To ask a follow-up: reuse the previous session_id and provide your follow-up query.
- Each response will include the session_id to use for subsequent follow-ups.
""")
async def analyze(
    file: UploadFile = File(None),
    text: Optional[str] = Form(None, description="Your query or context (optional)"),
    session_id: Optional[str] = Form(None, description="Session/thread ID for follow-ups (optional)"),
    feature_toggle: bool = Form(False),
    narrative_toggle: bool = Form(False),
):
    trace_id = str(uuid.uuid4())
    log.info(
        "/analyze endpoint called",
        feature_toggle=feature_toggle,
        narrative_toggle=narrative_toggle,
        text=text,
        file=bool(file and getattr(file, 'filename', None)),
        session_id=session_id,
        trace_id=trace_id,
    )

    # --- Input Validation ---
    if (not file or not getattr(file, 'filename', None)) and not (text and text.strip()):
        return JSONResponse(
            status_code=400,
            content=AnalyzeResponse(
                status="error",
                session_id=session_id or "",
                message="You must provide at least a file or a text query."
            ).model_dump(),
        )

    # --- Session/Thread Logic ---
    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = True
    else:
        new_session = False
    user_id = "user1"  # For now, static; could be enhanced for auth/multi-user

    # --- Build Agent Input ---
    parts = []
    user_message = text.strip() if text and text.strip() else None
    if not user_message and file and getattr(file, 'filename', None):
        user_message = f"Please analyze the attached file: {file.filename}"
    if user_message:
        parts.append(Part.from_text(text=user_message))
    parts.append(Part.from_text(text=f"Feature Toggle: {feature_toggle}"))
    parts.append(Part.from_text(text=f"Narrative Toggle: {narrative_toggle}"))
    if file and getattr(file, 'filename', None):
        await file.seek(0)
        file_content = await file.read()
        # Map file extension to supported MIME type
        ext = os.path.splitext(file.filename)[-1].replace('.', '').lower()
        mime_type_map = {
            "csv": "text/csv",
            "pdf": "application/pdf",
            "txt": "text/plain"
        }
        if ext not in mime_type_map:
            return JSONResponse(
                status_code=400,
                content=AnalyzeResponse(
                    status="error",
                    session_id=session_id or "",
                    message=f"Unsupported file type: .{ext}. Only CSV, PDF, and TXT files are supported."
                ).model_dump(),
            )
        mime_type = mime_type_map[ext]
        import base64
        if ext in ("csv", "pdf", "xlsx", "xls"):
            encoded_content = base64.b64encode(file_content).decode("utf-8")
        elif ext == "txt":
            # Assume text file is utf-8 encoded
            encoded_content = file_content.decode("utf-8")
        else:
            encoded_content = base64.b64encode(file_content).decode("utf-8")
        # Only send the base64-encoded content as a text part for the agent's tool
        parts.append(Part.from_text(text=f"Uploaded file: {file.filename}"))
        parts.append(Part.from_text(text=encoded_content))
    content = Content(parts=parts)

    # --- Create Session (local only) ---
    try:
        if hasattr(runner, "session_service"):
            await runner.session_service.create_session(session_id=session_id, user_id=user_id, app_name="AIE")
    except ValueError:
        log.warning(
            "Attempted to create a session that already exists.",
            session_id=session_id,
            trace_id=trace_id,
        )
        pass

    # --- Agent Invocation ---
    final_response_text = ""
    try:
        if hasattr(runner, "run_async"):
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
            input_str = text or ""
            from utils.vertex_agent_rest import call_vertex_agent_rest
            result = call_vertex_agent_rest(input_str)
            log.info(
                "Agent returned final response.",
                response=result,
                trace_id=trace_id,
            )
            if isinstance(result, dict):
                if 'error' in result:
                    return AnalyzeResponse(
                        status="error",
                        session_id=session_id,
                        message=result['error'],
                    )
                elif 'tool_calls' in result:
                    return AnalyzeResponse(
                        status="success",
                        session_id=session_id,
                        result={"tool_calls": result['tool_calls']},
                        message="Analysis complete.",
                    )
                else:
                    return AnalyzeResponse(
                        status="success",
                        session_id=session_id,
                        result={"analysis": result.get('text', '')},
                        message="Analysis complete.",
                    )
            else:
                return AnalyzeResponse(
                    status="success",
                    session_id=session_id,
                    result={"analysis": result},
                    message="Analysis complete.",
                )

        if not final_response_text:
            log.warning("Agent did not return a final response.", trace_id=trace_id)
            return JSONResponse(
                status_code=500,
                content=AnalyzeResponse(
                    status="error", session_id=session_id, message="Agent did not produce a final response."
                ).model_dump(),
            )

        return AnalyzeResponse(
            status="success",
            session_id=session_id,
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
            content=AnalyzeResponse(
                status="error", session_id=session_id, message=f"An internal error occurred: {str(e)}"
            ).model_dump(),
        )


@app.get("/")
def root():
    return {"message": "Adaptive Insight Engine API is running."}