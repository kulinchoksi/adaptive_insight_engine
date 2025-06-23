import inspect
from collections.abc import Mapping, Iterable
from dataclasses import is_dataclass, asdict
from typing import Dict, Any
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


def serialize(obj, max_depth=3, _depth=0):
    """Recursively serialize object up to max_depth."""
    if _depth > max_depth:
        return repr(obj)
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if is_dataclass(obj):
        return serialize(asdict(obj), max_depth, _depth + 1)
    if isinstance(obj, Mapping):
        return {k: serialize(v, max_depth, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        return [serialize(v, max_depth, _depth + 1) for v in obj]
    if hasattr(obj, "__dict__"):
        return {k: serialize(v, max_depth, _depth + 1)
                for k, v in vars(obj).items()}
    # fallback
    return repr(obj)


def log_function_args(**kwargs):
    data = {}
    for key, value in kwargs.items():
        try:
            data[key] = serialize(value, max_depth=1)
        except Exception:
            data[key] = repr(value)
    # print("-------------------------------------")
    # print(json.dumps(data, indent=2, default=str))
    # print("-------------------------------------")


def log_function_args2(max_depth=1):
    frame = inspect.currentframe().f_back
    args, _, _, values = inspect.getargvalues(frame)
    data = {}
    for arg in args:
        try:
            data[arg] = serialize(values[arg], max_depth=max_depth)
        except Exception:
            data[arg] = repr(values[arg])
    # print("---------------[LOGGER_MANUAL] Function call arguments:")
    # print("-------------------------------------" + json.dumps(data, indent=2, default=str) + "  ----------------------------------")


def before_tool_modifier(
        tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Inspects/modifies tool args or skips the tool call."""
    log_function_args()
    agent_name = tool_context.agent_name
    tool_name = tool.name
    print(f"\n[---Callback-Tool---] Before tool call for tool '{tool_name}' in agent '{agent_name}' Original args: '{args}'\n")
    return None


def after_too_callback(
        tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """Inspects/modifies the tool result after execution."""
    log_function_args()
    agent_name = tool_context.agent_name
    tool_name = tool.name
    print(
        f"\n[---Callback-Tool---] After tool call for tool '{tool_name}' in agent '{agent_name}' Args used: {args} tool_response: {tool_response}\n")
    return None


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Logs entry and checks 'skip_llm_agent' in session state.
    If True, returns Content to skip the agent's execution.
    If False or not present, returns None to allow execution.
    """
    log_function_args(arg1=callback_context)
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()

    print(
        f"\n[---Callback-Agent---] Entering agent: {agent_name} (Inv: {invocation_id}) Current State: {current_state} use-context: {callback_context._invocation_context.user_content}\n")

    # Return None to allow the LlmAgent's normal execution
    return None


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Logs exit from an agent and checks 'add_concluding_note' in session state.
    If True, returns new Content to *replace* the agent's original output.
    If False or not present, returns None, allowing the agent's original output to be used.
    """
    log_function_args(arg1=callback_context)
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()

    print(
        f"\n[---Callback-Agent---] Exiting agent: {agent_name} (Inv: {invocation_id}) Current State: {current_state} {callback_context.user_content}\n")
    return None


def before_model_callback(
        callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    log_function_args()
    agent_name = callback_context.agent_name
    # print(f"[---Callback---] Before model call for agent: {agent_name} with tools: {llm_request.tools_dict}")

    # Inspect the last user message in the request contents
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(
        f"\n[---Callback-LLM---] Before model call for agent: {agent_name} with tools: {llm_request.tools_dict} last user message: {last_user_message}\n")

    # Return None to allow the (modified) request to go to the LLM
    return None


def after_model_callback(
        callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM response after it's received."""
    log_function_args()
    agent_name = callback_context.agent_name
    print(f"\n[---Callback-LLM---] After model call for agent: {agent_name} llm response: {llm_response.content}\n")
    return None  # Nothing to modify
