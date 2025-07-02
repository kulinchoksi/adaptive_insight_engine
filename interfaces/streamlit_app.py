import streamlit as st
import os
import asyncio
import structlog
from dotenv import load_dotenv
from google.genai import types
from aie_agents.agent import workflow_orchestrator_agent
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
        return Runner(agent=workflow_orchestrator_agent, app_name="AIE", session_service=session_service)

def main():
    load_dotenv()
    logger = structlog.get_logger("StreamlitApp")
    st.set_page_config(page_title="Adaptive Insight Engine", layout="wide")
    st.title("Adaptive Insight Engine (AIE)")
    st.write("A modular, extensible GenAI multi-agent Data Analysissystem.")
    # Hide Streamlit's default file uploader message
    st.markdown('''<style>
    .element-container:has(.stFileUploader) label ~ div > div > div[data-testid="stFileUploaderDropzone"] + div {
        display: none !important;
    }
    .custom-upload-caption {
        color: #666;
        font-size: 0.9em;
        margin-top: -10px;
        margin-bottom: 10px;
    }
    </style>''', unsafe_allow_html=True)

    # st.markdown("""
    # ### How to use this app
    # - **Upload a file** (CSV, Excel, PDF), **enter a text query**, or **both**.
    # - Example 1: *Upload a sales.csv file and click Run Analysis to get sales insights.*
    # - Example 2: *Enter 'Analyze quarterly revenue trends' by providing relevant data in text and click Run Analysis.*
    # - Example 3: *Upload a file and enter 'Focus on Q4 data' for a targeted analysis.*
    # - **Analysis will only start when you provide clear, valid input.**
    # - If your input is unclear or missing, you'll see an error and can correct it before proceeding.
    # """)

    # --- Session State for Chat History ---
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []  # Each item: {'role': 'user'|'agent', 'text': str, 'file': file or None}
    if 'session_id' not in st.session_state:
        st.session_state.session_id = os.urandom(8).hex()

    # --- Sidebar Config ---
    st.sidebar.header("Configuration")
    feature_toggle = st.sidebar.checkbox("Enable Contextualytics (external data enrichment)")
    narrative_toggle = st.sidebar.checkbox("Enable NarrativeAI (storytelling)")
    # 'New Analysis' button moved to input form

    # --- Main Chat Area ---
    st.markdown("#### Conversation")
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            with st.chat_message("user"):
                if msg.get('file_name'):
                    st.write(f"**User uploaded file:** {msg['file_name']}")
                st.write(msg['text'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['text'])

    # --- Input Area ---
    with st.form(key="chat_input_form", clear_on_submit=True):
        cols = st.columns([3, 2])
        with cols[0]:
            user_input = st.text_area("Enter your query or context (optional)", height=80, key="user_input")
        with cols[1]:
            uploaded_file = st.file_uploader("Upload a file (optional)", type=["csv"], key="file_uploader")
            st.markdown('<div class="custom-upload-caption">Limit 2 MB per file • CSV</div>', unsafe_allow_html=True)
        # Disable 'Send' if last message is from agent (i.e., analysis complete)
        disable_send = False
        if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'agent':
            disable_send = True
        send_col, new_col = st.columns([1, 1])
        with send_col:
            submitted = st.form_submit_button("Send", disabled=disable_send)
        with new_col:
            new_analysis_clicked = st.form_submit_button("New Analysis")
        if new_analysis_clicked:
            st.session_state.clear()
            st.rerun()

    # --- Validation ---
    input_is_valid = bool(user_input.strip() or uploaded_file)
    if submitted:
        if not input_is_valid:
            st.warning("Please provide a file and/or enter a query before sending.")
        else:
            # Add user message to chat history
            file_bytes = None
            if uploaded_file is not None:
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
            msg = {'role': 'user', 'text': user_input.strip(), 'file_name': uploaded_file.name if uploaded_file else None, 'file_bytes': file_bytes}
            st.session_state.chat_history.append(msg)
            st.rerun()  # Rerun to show user message before agent response

    # --- Agent Response Trigger ---
    # Only trigger agent if last message is user and not yet answered
    runner = get_agent_runner()
    if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'user':
        last_msg = st.session_state.chat_history[-1]
        # Only run agent if not already answered
        if len(st.session_state.chat_history) < 2 or st.session_state.chat_history[-2]['role'] != 'agent':
            with st.spinner("Agent is analysing..."):
                # Prepare input
                user_text = last_msg['text']
                file_bytes = last_msg.get('file_bytes')
                file_name = last_msg.get('file_name')
                file_type = os.path.splitext(file_name)[-1].replace(".", "").lower() if file_name else None
                async def get_agent_response():
                    user_id = "user1"
                    session_id = st.session_state.session_id
                    app_name = "AIE"
                    if hasattr(runner, "session_service"):
                        await runner.session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
                    parts = []
                    if user_text:
                        parts.append(types.Part(text=user_text))
                    parts.append(types.Part(text=f"Feature Toggle: {feature_toggle}"))
                    parts.append(types.Part(text=f"Narrative Toggle: {narrative_toggle}"))
                    if file_bytes:
                        # Map file extension to supported MIME type
                        mime_type_map = {
                            "csv": "text/csv",
                            # "pdf": "application/pdf",
                            # "txt": "text/plain"
                        }
                        if file_type not in mime_type_map:
                            st.error(f"Unsupported file type: .{file_type}. Only CSV files are supported.")
                            return  # Prevent agent call
                        parts.append(types.Part(text=f"Uploaded file: {file_name}"))
                        parts.append(types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type_map[file_type],
                                data=file_bytes
                            )
                        ))
                    content = types.Content(role="user", parts=parts)
                    final_response_text = "Agent did not produce a final response."
                    if hasattr(runner, "run_async"):
                        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
                            if event.is_final_response() and event.content and event.content.parts:
                                final_response_text = event.content.parts[0].text
                    else:
                        input_str = user_text or ""
                        from utils.vertex_agent_rest import call_vertex_agent_rest
                        final_response_text = call_vertex_agent_rest(input_str)
                    return final_response_text
                from google.genai.errors import ClientError
                try:
                    result = asyncio.run(get_agent_response())
                except ClientError as e:
                    if "token count" in str(e) or "model only supports up to" in str(e):
                        result = ("The data or prompt is too large for the AI model to process. "
                                  "Please try with a smaller file, or start a new session if you want to analyze a new file.")
                    else:
                        result = f"An error occurred: {e}"
                except Exception as e:
                    result = f"An error occurred: {e}"
                st.session_state.chat_history.append({'role': 'agent', 'text': result})
                st.rerun()

    st.info("Refreshing or starting a new analysis will clear previous results and context (memory). Each run is independent.")

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
    st.markdown("---")
    st.caption("Built with Streamlit, ADK, and Google Cloud. See README for details.")

if __name__ == "__main__":
    main()