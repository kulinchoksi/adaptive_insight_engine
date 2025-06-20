import streamlit as st
import os
import asyncio
import structlog
from dotenv import load_dotenv
from google.genai import types
from utils.logger import configure_logging
from adaptive_insight_engine.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# For remote agent access
try:
    from vertexai import agent_engines
except ImportError:
    agent_engines = None

load_dotenv()
RESOURCE_ID = os.getenv("RESOURCE_ID")
AGENT_BACKEND = os.getenv("AGENT_BACKEND", "local").lower()

def get_agent_runner():
    if AGENT_BACKEND == "vertexai" and RESOURCE_ID and agent_engines is not None:
        # Use remote agent from Vertex AI Agent Engine
        return agent_engines.get(RESOURCE_ID)
    else:
        # Use local agent
        session_service = InMemorySessionService()
        return Runner(agent=root_agent, app_name="AIE", session_service=session_service)

def main():
    load_dotenv()
    configure_logging()
    logger = structlog.get_logger("StreamlitApp")
    st.set_page_config(page_title="Adaptive Insight Engine", layout="wide")
    st.title("Adaptive Insight Engine (AIE)")
    st.write("A modular, extensible GenAI multi-agent system.")

    # File upload
    uploaded_file = st.file_uploader("Upload your data file (CSV, Excel, PDF)", type=["csv", "xlsx", "xls", "pdf"])
    file_type = None
    if uploaded_file is not None:
        file_type = os.path.splitext(uploaded_file.name)[-1].replace(".", "").lower()

    # Parameter selection (example)
    st.sidebar.header("Configuration")
    feature_toggle = st.sidebar.checkbox("Enable Contextualytics (external data enrichment)")
    narrative_toggle = st.sidebar.checkbox("Enable NarrativeAI (storytelling)")

    # Placeholder for follow-up query
    followup_query = st.text_input("Ask a follow-up question (optional)")

    # Results
    runner = get_agent_runner()

    async def get_agent_response(uploaded_file, file_type, feature_toggle, narrative_toggle, followup_query):
        user_id = "user1"
        session_id = "session1"
        app_name = "AIE"
        # Only create session if runner has session_service (local mode)
        if hasattr(runner, "session_service"):
            await runner.session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

        parts = []
        # Add text parts
        if followup_query:
            parts.append(types.Part(text=f"Follow-up: {followup_query}"))
        parts.append(types.Part(text=f"Feature Toggle: {feature_toggle}"))
        parts.append(types.Part(text=f"Narrative Toggle: {narrative_toggle}"))

        # Add file part if present
        if uploaded_file is not None:
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()
            parts.append(types.Part(inline_data=types.Blob(
                mime_type=uploaded_file.type or "application/octet-stream",
                data=file_bytes
            )))
        
        content = types.Content(role="user", parts=parts)
        final_response_text = "Agent did not produce a final response."
        if hasattr(runner, "run_async"):
            # Local agent: stream responses
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
        else:
            # Remote agent: use .query(input=...)
            input_str = ""
            for part in parts:
                if hasattr(part, "text") and part.text is not None:
                    input_str += part.text + "\n"
            from utils.vertex_agent_rest import call_vertex_agent_rest
            final_response_text = call_vertex_agent_rest(input_str)
        return final_response_text

    if st.button("Run Analysis"):
        if not uploaded_file and not followup_query:
            st.warning("Please upload a file or ask a question.")
        else:
            logger.info("Run Analysis triggered", feature_toggle=feature_toggle, narrative_toggle=narrative_toggle, followup_query=followup_query)
            st.info("Running analysis...")
            with st.spinner("Agent is thinking..."):
                result = asyncio.run(get_agent_response(uploaded_file, file_type, feature_toggle, narrative_toggle, followup_query))
            st.success("Analysis complete.")
            if isinstance(result, dict):
                if "errors" in result and result["errors"]:
                    st.error("Agent error: " + "\n".join(result["errors"]))
                if "tool_calls" in result and result["tool_calls"]:
                    st.info(f"Tool calls: {result['tool_calls']}")
                if "text" in result:
                    st.write(result["text"])
                elif "raw" in result:
                    st.write(result["raw"])
            else:
                st.write(result)

    st.markdown("---")
    st.caption("Built with Streamlit, ADK, and Google Cloud. See README for details.")

if __name__ == "__main__":
    main()