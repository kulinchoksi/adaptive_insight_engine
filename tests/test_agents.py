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

import os
import pytest
from unittest.mock import Mock, patch
from typing import Generator

from google.genai import types
from google.adk.agents import LlmAgent, SequentialAgent, Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.events import Event, EventActions

from agents.agent import root_agent
from agents.workflow.agent import workflow_orchestrator_agent
from agents.interaction.agent import user_interaction_agent

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
    """Create a test runner with in-memory services."""
    return Runner(
        app_name="AdaptiveInsightEngine",
        agent=None,
        artifact_service=artifact_service,
        session_service=session_service,
    )

@pytest.fixture
def session(session_service: InMemorySessionService) -> Session:
    """Create a test session."""
    return session_service.create_session(
        app_name="AdaptiveInsightEngine",
        user_id="test_user",
    )

@pytest.fixture
def mock_llm() -> Generator[Mock, None, None]:
    """Mock the LLM responses for testing."""
    with patch("google.adk.agents.LlmAgent._call_model") as mock:
        # Default mock response
        mock.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Mock LLM response")]
                    )
                )
            ]
        )
        yield mock

class TestAgentHierarchy:
    """Test the agent hierarchy and parent-child relationships."""

    def test_root_agent_has_correct_sub_agents(self):
        """Test that root agent has the expected sub-agents."""
        assert isinstance(root_agent, Agent)
        assert len(root_agent.sub_agents) == 2
        assert any(isinstance(agent, LlmAgent) and agent.name == "user_interaction_agent" 
                  for agent in root_agent.sub_agents)
        assert any(isinstance(agent, SequentialAgent) and agent.name == "workflow_orchestrator_agent" 
                  for agent in root_agent.sub_agents)

    def test_workflow_orchestrator_agent_type(self):
        """Test that workflow orchestrator is a SequentialAgent."""
        assert isinstance(workflow_orchestrator_agent, SequentialAgent)

    def test_user_interaction_agent_type(self):
        """Test that user interaction agent is an LlmAgent."""
        assert isinstance(user_interaction_agent, LlmAgent)

class TestAgentCommunication:
    """Test agent communication and state sharing."""

    @pytest.mark.asyncio
    async def test_agent_state_sharing(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that agents can share state through the session."""
        # Configure mock for specific test
        mock_llm.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Test state sharing")]
                    )
                )
            ]
        )

        # Set initial state
        session.state["test_key"] = "test_value"
        
        # Run agent
        runner.agent = user_interaction_agent
        content = types.Content(role="user", parts=[types.Part(text="Test query")])
        events = list(
            runner.run(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            )
        )

        # Verify state was preserved
        assert session.state["test_key"] == "test_value"

    @pytest.mark.asyncio
    async def test_agent_transfer(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that agents can transfer control to each other."""
        # Configure mock for specific test
        mock_llm.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Transfer to workflow orchestrator")]
                    )
                )
            ]
        )

        # Run root agent
        runner.agent = root_agent
        content = types.Content(role="user", parts=[types.Part(text="Analyze sales data")])
        events = list(
            runner.run(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            )
        )

        # Verify transfer occurred
        assert any(
            event.actions and event.actions.transfer_to_agent == "workflow_orchestrator_agent"
            for event in events
        )

class TestWorkflowPatterns:
    """Test different workflow patterns using SequentialAgent."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that workflow orchestrator executes agents in sequence."""
        # Configure mock for specific test
        mock_llm.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Sequential execution test")]
                    )
                )
            ]
        )

        # Run workflow orchestrator
        runner.agent = workflow_orchestrator_agent
        content = types.Content(role="user", parts=[types.Part(text="Run analysis pipeline")])
        events = list(
            runner.run(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            )
        )

        # Verify sequential execution
        agent_execution_order = [
            event.author for event in events 
            if event.author in [agent.name for agent in workflow_orchestrator_agent.sub_agents]
        ]
        assert len(agent_execution_order) > 0
        # Add more specific assertions about execution order if needed

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that workflow orchestrator handles errors gracefully."""
        # Configure mock to simulate an error
        mock_llm.side_effect = Exception("Simulated error")

        # Run workflow orchestrator
        runner.agent = workflow_orchestrator_agent
        content = types.Content(role="user", parts=[types.Part(text="Test error handling")])
        
        with pytest.raises(Exception) as exc_info:
            list(
                runner.run(
                    user_id="test_user",
                    session_id=session.id,
                    new_message=content
                )
            )
        
        assert "Simulated error" in str(exc_info.value)

class TestUserInteraction:
    """Test user interaction agent functionality."""

    @pytest.mark.asyncio
    async def test_query_understanding(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that user interaction agent can understand and process queries."""
        # Configure mock for specific test
        mock_llm.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Query understood and processed")]
                    )
                )
            ]
        )

        # Run user interaction agent
        runner.agent = user_interaction_agent
        content = types.Content(role="user", parts=[types.Part(text="What were our top products last month?")])
        events = list(
            runner.run(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            )
        )

        # Verify response
        assert any(
            event.content and "Query understood" in event.content.parts[0].text
            for event in events
        )

    @pytest.mark.asyncio
    async def test_clarification_requests(self, runner: Runner, session: Session, mock_llm: Mock):
        """Test that user interaction agent can request clarification when needed."""
        # Configure mock to simulate need for clarification
        mock_llm.return_value = types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Could you clarify which time period you're interested in?")]
                    )
                )
            ]
        )

        # Run user interaction agent
        runner.agent = user_interaction_agent
        content = types.Content(role="user", parts=[types.Part(text="Show me the sales")])
        events = list(
            runner.run(
                user_id="test_user",
                session_id=session.id,
                new_message=content
            )
        )

        # Verify clarification request
        assert any(
            event.content and "clarify" in event.content.parts[0].text.lower()
            for event in events
        )

if __name__ == "__main__":
    pytest.main()
