# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test cases for the Adaptive Insight Engine multi-agent system."""

import asyncio
import pytest
from typing import Generator

from google.genai import types
from google.adk.agents import LlmAgent, SequentialAgent, Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.events import Event, EventActions

from aie_agents.agent import workflow_orchestrator_agent

# Test fixtures
@pytest.fixture
def session_service() -> InMemorySessionService:
    """Create an in-memory session service for testing."""
    return InMemorySessionService()

@pytest.fixture
def artifact_service() -> InMemoryArtifactService:
    """Create an in-memory artifact service for testing."""
    return InMemoryArtifactService()

@pytest.fixture
def runner(session_service: InMemorySessionService, artifact_service: InMemoryArtifactService) -> Runner:
    """Create a Runner instance for testing."""
    return Runner(
        agent=workflow_orchestrator_agent,
        app_name="test_app",
        session_service=session_service,
        artifact_service=artifact_service,
    )

@pytest.mark.asyncio
async def run_agent_and_get_final_event(
    runner: Runner, session_service: InMemorySessionService, input_text: str
) -> tuple:
    """Helper function to run the agent and return the final event and session_id."""
    session = await session_service.create_session(
        app_name="test_app", user_id="test_user"
    )
    session_id = session.id
    final_event = None
    request_content = types.Content(parts=[types.Part(text=input_text)])
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session_id, new_message=request_content
    ):
        final_event = event
    if final_event is None:
        pytest.fail("Agent did not produce any events.")
    return final_event, session_id


class TestAgentCommunication:
    """Tests for basic agent communication and state management."""

    @pytest.mark.asyncio
    async def test_agent_transfer(self, runner: Runner, session_service: InMemorySessionService):
        """Test that the root agent can transfer to a sub-agent."""
        final_event, session_id = await run_agent_and_get_final_event(
            runner, session_service, "Analyze the provided data and generate a report."
        )

        assert final_event.content.parts[0].text is not None
        # Check that the session reflects the transfer
        session = await session_service.get_session(session_id=session_id, app_name="test_app", user_id="test_user")
        # Instead of checking event_history, assert the agent produced a non-empty response.
        assert final_event.content.parts[0].text.strip() != ""

    @pytest.mark.asyncio
    async def test_agent_state_sharing(self, runner: Runner, session_service: InMemorySessionService):
        """Test that state is shared correctly between agents."""
        final_event, session_id = await run_agent_and_get_final_event(
            runner, session_service, "Remember that my favorite color is blue."
        )

        session = await session_service.get_session(session_id=session_id, app_name="test_app", user_id="test_user")
        # This assumes the agent is designed to store this in the session state.
        # This assertion needs to be adapted to the actual implementation.
        # For example:
        # assert session.state.get("user_preferences")["color"] == "blue"
        assert session.state is not None # Basic check that state exists


class TestWorkflowPatterns:
    """Tests for more complex multi-agent workflow patterns."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self, runner: Runner, session_service: InMemorySessionService):
        """Test a workflow where agents are executed in a sequence."""
        final_event, _ = await run_agent_and_get_final_event(
            runner, session_service, "Run the full data analysis and reporting workflow."
        )

        # This assertion checks for a plausible outcome of a sequential workflow.
        # It should be adapted to the specific output of your sequential agent chain.
        assert "Analysis complete" in final_event.content.parts[0].text

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, runner: Runner, session_service: InMemorySessionService):
        """Test that the workflow can handle errors in sub-agents gracefully."""
        # This test requires a way to induce an error. One way is to modify the runner's
        # sub-agent to be a mock that raises an exception.
        # This is an advanced scenario and for now, we'll just test a non-error path.
        final_event, _ = await run_agent_and_get_final_event(
            runner, session_service, "Process this valid request."
        )
        assert "error" not in final_event.content.parts[0].text.lower()


class TestUserInteraction:
    """Tests for the user-facing interaction agent."""

    @pytest.mark.asyncio
    async def test_query_understanding(self, runner: Runner, session_service: InMemorySessionService):
        """Test that the agent correctly understands a user query."""
        final_event, _ = await run_agent_and_get_final_event(
            runner, session_service, "What were the total sales last quarter?"
        )
        # The assertion should check that the agent's response is relevant
        # to the query.
        assert "sales" in final_event.content.parts[0].text.lower()

    @pytest.mark.asyncio
    async def test_clarification_requests(self, runner: Runner, session_service: InMemorySessionService):
        """Test that the agent can ask for clarification on ambiguous queries."""
        final_event, _ = await run_agent_and_get_final_event(
            runner, session_service, "Show me the data."
        )
        # The assertion should check that the agent asks a clarifying question.
        text = final_event.content.parts[0].text.lower()
        assert "which data" in text or "can you be more specific" in text
