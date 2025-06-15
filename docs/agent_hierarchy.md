# Adaptive Insight Engine Agent Hierarchy

## Agent Tree Structure
```
Root Agent (LlmAgent)
├── User Interaction Agent (LlmAgent)
│   ├── Query Understanding
│   │   └── Tools: query_parser, intent_classifier, context_builder
│   └── User Communication
│       └── Tools: response_formatter, clarification_handler, feedback_processor
└── Workflow Orchestrator (SequentialAgent)
    ├── Data Ingestion Agent (LlmAgent)
    │   ├── Data Validation
    │   │   └── Tools: format_validator, schema_validator, quality_checker
    │   └── Preprocessing
    │       └── Tools: data_cleaner, feature_engineer, metadata_extractor
    ├── Analysis Agent (LlmAgent)
    │   ├── Core Analysis
    │   │   └── Tools: statistical_analyzer, trend_detector, correlation_finder
    │   └── External Context
    │       └── Tools: external_data_fetcher, context_integrator, relevance_scorer
    ├── Simulation Agent (LlmAgent)
    │   ├── Scenario Management
    │   │   └── Tools: scenario_builder, parameter_manager, constraint_validator
    │   └── What-if Analysis
    │       └── Tools: impact_analyzer, sensitivity_tester, result_validator
    └── Insight Synthesis Agent (LlmAgent)
        ├── Insight Generation
        │   └── Tools: insight_extractor, pattern_recognizer, recommendation_generator
        └── Explanation Tracing
            └── Tools: explanation_builder, trace_collector, narrative_formatter
```

## Agent Roles and Responsibilities

### Root Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: Top-level coordinator and delegator
- **Responsibilities**:
  - Initial request handling
  - Task delegation to sub-agents
  - High-level workflow coordination
  - Error handling and recovery

### User Interaction Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: User communication and query understanding
- **Responsibilities**:
  - Natural language query processing
  - User intent understanding
  - Clarification requests
  - Response formatting

### Workflow Orchestrator
- **Type**: SequentialAgent
- **Role**: Pipeline execution coordinator
- **Responsibilities**:
  - Sequential execution of analysis pipeline
  - State management between agents
  - Error handling and recovery
  - Pipeline monitoring

### Data Ingestion Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: Data processing and validation
- **Responsibilities**:
  - Data file ingestion
  - Format validation
  - Data cleaning
  - Metadata extraction

### Analysis Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: Core analysis and external context
- **Responsibilities**:
  - Statistical analysis
  - External data integration
  - Correlation analysis
  - Trend identification

### Simulation Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: Scenario analysis
- **Responsibilities**:
  - What-if scenario execution
  - Parameter management
  - Impact analysis
  - Result validation

### Insight Synthesis Agent
- **Type**: LlmAgent
- **Model**: gemini-2.0-pro
- **Role**: Insight generation and explanation
- **Responsibilities**:
  - Insight generation
  - Narrative creation
  - Explanation tracing
  - Recommendation synthesis

## Agent Communication Patterns

### Inter-Agent Communication
1. **Direct Communication**
   - Root Agent ↔ User Interaction Agent
   - Root Agent ↔ Workflow Orchestrator
   - Workflow Orchestrator ↔ All Sub-Agents

2. **State Management**
   - Shared State: Common data and context
   - Agent State: Individual agent context
   - Workflow State: Pipeline execution state

3. **Message Types**
   ```python
   {
       "type": "request|response|error|state_update",
       "sender": "agent_name",
       "recipient": "agent_name",
       "content": {
           "action": "action_name",
           "parameters": {},
           "context": {},
           "state": {}
       },
       "metadata": {
           "timestamp": "ISO timestamp",
           "trace_id": "unique_id",
           "priority": "high|normal|low"
       }
   }
   ```

## Agent-Specific Tools and Capabilities

### Root Agent Tools
- `task_delegator`: Routes tasks to appropriate agents
- `state_manager`: Maintains global system state
- `error_handler`: Coordinates error recovery
- `workflow_monitor`: Tracks pipeline execution

### User Interaction Agent Tools
- `query_parser`: Parses and structures user queries
- `intent_classifier`: Identifies user intent
- `context_builder`: Builds conversation context
- `response_formatter`: Formats agent responses
- `clarification_handler`: Manages clarification requests
- `feedback_processor`: Processes user feedback

### Data Ingestion Agent Tools
- `format_validator`: Validates input data formats
- `schema_validator`: Validates data schema
- `quality_checker`: Assesses data quality
- `data_cleaner`: Cleans and normalizes data
- `feature_engineer`: Creates derived features
- `metadata_extractor`: Extracts data metadata

### Analysis Agent Tools
- `statistical_analyzer`: Performs statistical analysis
- `trend_detector`: Identifies trends and patterns
- `correlation_finder`: Finds correlations
- `external_data_fetcher`: Fetches external data
- `context_integrator`: Integrates external context
- `relevance_scorer`: Scores data relevance

### Simulation Agent Tools
- `scenario_builder`: Builds simulation scenarios
- `parameter_manager`: Manages simulation parameters
- `constraint_validator`: Validates constraints
- `impact_analyzer`: Analyzes scenario impacts
- `sensitivity_tester`: Tests parameter sensitivity
- `result_validator`: Validates simulation results

### Insight Synthesis Agent Tools
- `insight_extractor`: Extracts key insights
- `pattern_recognizer`: Recognizes patterns
- `recommendation_generator`: Generates recommendations
- `explanation_builder`: Builds explanations
- `trace_collector`: Collects execution traces
- `narrative_formatter`: Formats narratives

## Environment Variables

### Required Variables
```env
# Model Configuration
ROOT_AGENT_MODEL=gemini-2.0-pro
USER_INTERACTION_MODEL=gemini-2.0-pro
ANALYSIS_AGENT_MODEL=gemini-2.0-pro
SIMULATION_AGENT_MODEL=gemini-2.0-pro
INSIGHT_AGENT_MODEL=gemini-2.0-pro

# Agent Configuration
MAX_AGENT_MEMORY=1000
AGENT_TIMEOUT=300
AGENT_RETRY_ATTEMPTS=3
AGENT_BACKOFF_FACTOR=2

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_REGION=us-central1

# API Configuration
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=false

# Storage Configuration
STORAGE_BUCKET=your-bucket-name
STATE_STORAGE_PATH=agent_states/
CACHE_STORAGE_PATH=cache/

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
LOG_FORMAT=json
LOG_STORAGE_PATH=logs/
```

### Optional Variables
```env
# Performance Tuning
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_ENABLED=true
CACHE_TTL=3600
MEMORY_LIMIT=1024

# Feature Flags
ENABLE_EXTERNAL_DATA=true
ENABLE_SIMULATION=true
ENABLE_EXPLANATION_TRACING=true
ENABLE_AGENT_MONITORING=true
ENABLE_STATE_PERSISTENCE=true

# Monitoring
ENABLE_METRICS=true
METRICS_EXPORT_INTERVAL=60
METRICS_STORAGE_PATH=metrics/
ALERT_THRESHOLD=0.95

# Agent-Specific Settings
USER_INTERACTION_MAX_TURNS=5
ANALYSIS_BATCH_SIZE=1000
SIMULATION_MAX_SCENARIOS=10
INSIGHT_MIN_CONFIDENCE=0.8
```

## Error Handling and Logging

### Logging Levels
- ERROR: Critical failures requiring immediate attention
- WARNING: Potential issues that don't stop execution
- INFO: Normal operation events
- DEBUG: Detailed debugging information

### Error Categories
1. **Input Validation Errors**
   - Invalid file formats
   - Missing required parameters
   - Malformed queries

2. **Processing Errors**
   - Data processing failures
   - Analysis computation errors
   - External API failures

3. **System Errors**
   - Resource exhaustion
   - Network failures
   - Authentication issues

4. **Business Logic Errors**
   - Invalid business rules
   - Constraint violations
   - Unsupported operations

### Error Response Format
```python
{
    "status": "error",
    "error_type": "category",
    "error_code": "specific_code",
    "message": "Human readable message",
    "details": {
        "context": "Additional context",
        "timestamp": "ISO timestamp",
        "trace_id": "Unique trace identifier"
    }
}
```

## Agent State Management

### State Types
1. **Global State**
   - System configuration
   - Shared resources
   - Global metrics
   - User session data

2. **Agent State**
   - Agent configuration
   - Current context
   - Execution history
   - Resource usage

3. **Workflow State**
   - Pipeline progress
   - Intermediate results
   - Dependencies
   - Execution metrics

### State Operations
```python
{
    "operation": "create|read|update|delete",
    "state_type": "global|agent|workflow",
    "key": "state_key",
    "value": "state_value",
    "metadata": {
        "timestamp": "ISO timestamp",
        "agent": "agent_name",
        "ttl": "time_to_live"
    }
}
```

### State Persistence
- In-memory cache for active states
- Persistent storage for long-term states
- State versioning and rollback
- State cleanup and garbage collection 