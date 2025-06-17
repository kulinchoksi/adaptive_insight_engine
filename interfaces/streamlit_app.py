import streamlit as st
import os
import asyncio
import structlog
from dotenv import load_dotenv
from google.genai import types
from utils.logger import configure_logging
from agents.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Placeholder for agent import
# from agents.user_interaction_agent import UserInteractionAgent

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
    runner = Runner(agent=root_agent, app_name="AIE", session_service=InMemorySessionService())

    async def get_agent_response(uploaded_file, file_type, feature_toggle, narrative_toggle, followup_query):
        user_id = "user1"
        session_id = "session1"
        app_name = "AIE"
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
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
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
            st.write(result)

    st.markdown("---")
    st.caption("Built with Streamlit, ADK, and Google Cloud. See README for details.")

if __name__ == "__main__":
    main()