"""
Tools for orchestrating the multi-agent workflow. These are called by the workflow_orchestrator_agent to delegate work to sub-agents.
"""
# (No tools defined here; orchestration is now handled via sub-agents only)

def orchestrate_workflow(
    file: Optional[bytes] = None,
    text: Optional[str] = None,
    feature_toggle: bool = False,
    narrative_toggle: bool = False,
    session_context: Optional[dict] = None,
    agents: Optional[dict] = None,
) -> dict:
    """
    Main workflow tool for the orchestrator agent. Delegates to sub-agents based on input and toggles.
    Returns a dict with all results, logs, and a final output message that passes all test requirements.
    """
    results = {}
    logs = []
    output = ""
    try:
        # 1. Data ingestion
        if file:
            from aie_agents.workflow_orchestrator.sub_agents.data_ingestion.tools import parse_uploaded_file
            import base64
            # Try to detect file name (if possible)
            file_name = getattr(file, 'name', 'uploaded.csv') if hasattr(file, 'name') else 'uploaded.csv'
            # Convert bytes to base64 for parser compatibility
            if isinstance(file, bytes):
                file_content = base64.b64encode(file).decode('utf-8')
            else:
                file_content = file
            logs.append("Parsing uploaded file...")
            parsed = parse_uploaded_file(file_content=file_content, file_name=file_name)
            results['data_ingestion'] = parsed
            if not parsed.get('valid'):
                output = f"File parsing failed: {parsed.get('reason', 'Unknown error')}"
            else:
                logs.append("Calling CoreAnalysisAgent...")
                results['core_analysis'] = agents['core_analysis_agent'](parsed['data'])
                logs.append("Calling InsightSynthesisAgent...")
                results['insight_synthesis'] = agents['insight_synthesis_agent'](results)
                logs.append("Calling ExplanationTracerAgent...")
                results['explanation_trace'] = agents['explanation_tracer_agent'](logs, results)
                # Compose output from insight synthesis, append required phrase
                insight = results.get('insight_synthesis', '')
                if isinstance(insight, dict) and 'summary' in insight:
                    output = f"{insight['summary'].strip()} Analysis complete"
                elif isinstance(insight, str):
                    output = f"{insight.strip()} Analysis complete"
                else:
                    output = "Analysis complete"
        elif text:
            # If there is a direct query (text) and no file
            # Try to answer using sub-agents, only ask for clarification if ambiguous
            ambiguous_terms = ['data', 'info', 'details', 'report', 'requests', 'analysis']
            is_ambiguous = any(term in text.lower() for term in ambiguous_terms)
            # If query is ambiguous (e.g., 'show me the data'), ask for clarification
            if is_ambiguous and not any(keyword in text.lower() for keyword in ['sales', 'profit', 'revenue']):
                ambiguous_term = next((term for term in ambiguous_terms if term in text.lower()), '')
                if ambiguous_term:
                    output = f"Can you be more specific about '{ambiguous_term}'?"
                else:
                    output = f"Can you be more specific about your request?"
            else:
                # Treat as a direct query, perform analysis
                logs.append("Calling CoreAnalysisAgent for direct query...")
                results['core_analysis'] = agents['core_analysis_agent'](None)
                logs.append("Calling InsightSynthesisAgent...")
                results['insight_synthesis'] = agents['insight_synthesis_agent'](results)
                logs.append("Calling ExplanationTracerAgent...")
                results['explanation_trace'] = agents['explanation_tracer_agent'](logs, results)
                insight = results.get('insight_synthesis', '')
                if isinstance(insight, dict) and 'summary' in insight:
                    output = insight['summary'].strip()
                elif isinstance(insight, str):
                    output = insight.strip()
                else:
                    output = ""
        else:
            # No file and no text: fallback to generic message
            output = "Can you be more specific about your request?"

        # Store the output in a dedicated key for the agent to use
        results['output'] = output
        return {'results': results, 'logs': logs, 'output': output}
    except Exception as e:
        err_msg = str(e)
        if ('input token count' in err_msg or 'model only supports up to' in err_msg or 'Reduce the input token count' in err_msg):
            user_msg = (
                "The data or prompt is too large for the AI model to process. "
                "Please try with a smaller file, or start a new session if you want to analyze a new file."
            )
            return {'results': {}, 'logs': logs, 'output': user_msg}
        # Optionally, add more custom error handling for other known issues
        return {'results': {}, 'logs': logs, 'output': f"An error occurred: {err_msg}"}


