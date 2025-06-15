import streamlit as st
import os
from utils.logger import configure_logging
import structlog
from agents.root_agent import root_agent

# Placeholder for agent import
# from agents.user_interaction_agent import UserInteractionAgent

def main():
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
    if st.button("Run Analysis"):
        logger.info("Run Analysis triggered", feature_toggle=feature_toggle, narrative_toggle=narrative_toggle, followup_query=followup_query)
        st.info("Running analysis...")
        # Prepare input for the root agent
        input_data = {
            "file": uploaded_file,
            "file_type": file_type,
            "feature_toggle": feature_toggle,
            "narrative_toggle": narrative_toggle,
            "followup_query": followup_query,
        }
        result = root_agent.run(input_data=input_data)
        st.success("Analysis complete.")
        st.write(result)

    st.markdown("---")
    st.caption("Built with Streamlit, ADK, and Google Cloud. See README for details.")

if __name__ == "__main__":
    main() 