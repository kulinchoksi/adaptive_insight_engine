import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()


def create_llm_client(agent: str):
    gemini_2_0_flash_lite_001 = "gemini-2.0-flash-lite-001"
    # groq
    groq_meta_llama_scout = "groq/meta-llama/llama-4-scout-17b-16e-instruct"

    model_mappings = {
        "ROOT_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "WORKFLOW_ORCHESTRATOR_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "SIMULATION_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "QUERY_UNDERSTANDING_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "INSIGHT_SYNTHESIS_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "EXTERNAL_CONTEXT_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "EXPLANATION_TRACER_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "DATA_INGESTION_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "CORE_ANALYSIS_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        },
        "USER_INTERACTION_AGENT_MODEL": {
            "google": gemini_2_0_flash_lite_001,
            "groq": groq_meta_llama_scout
        }
    }

    providers = {
        "google": {
            "api_key": os.environ.get("GOOGLE_API_KEY"),
            "client": lambda model: model  # Google models are returned directly
        },
        "groq": {
            "api_key": os.environ.get("GROQ_API_KEY"),
            "client": lambda model: LiteLlm(model=model)
        },
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "client": lambda model: LiteLlm(model=model)
        },
    }

    if agent not in model_mappings:
        raise ValueError(f"Unsupported agent: {agent}. Please add it to the model mappings.")

    for provider_name, provider_info in providers.items():
        if provider_info["api_key"] and provider_name in model_mappings[agent]:
            model = model_mappings[agent][provider_name]
            print(f"Created client for an agent {agent} using {provider_name.capitalize()}'s {model} model.")
            return provider_info["client"](model)

    raise ValueError(f"No available API key or model mapping for agent: {agent}")
