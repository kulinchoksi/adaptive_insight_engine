import os
import json
import requests
from google import auth as google_auth
from google.auth.transport import requests as google_requests


def get_identity_token():
    credentials, _ = google_auth.default()
    auth_request = google_requests.Request()
    credentials.refresh(auth_request)
    return credentials.token


def call_vertex_agent_rest(input_str, resource_id=None, project_id=None, location=None, user_id=None):
    """
    Calls the deployed Vertex AI Agent Engine via REST API using stateless :streamQuery (preferred) or :query (fallback).
    Args:
        input_str: User query and context as a string.
        resource_id: The agent resource ID (short or full resource name).
        project_id: GCP Project ID (required if resource_id is not a full resource name).
        location: GCP region (required if resource_id is not a full resource name).
    Returns:
        Agent response as a string.
    """
    if resource_id is None:
        resource_id = os.getenv("RESOURCE_ID")
    if project_id is None:
        project_id = os.getenv("PROJECT_ID")
    if location is None:
        location = os.getenv("LOCATION")

    base = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/reasoningEngines/{resource_id}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {get_identity_token()}"
    }
    if not user_id:
        user_id = "anonymous"
    payload = {
        "class_method": "stream_query",
        "input": {
            "user_id": user_id,
            "message": input_str
        }
    }

    import json
    def parse_streaming_response(resp):
        texts = []
        tool_calls = []
        errors = []
        for line in resp.iter_lines():
            if line:
                try:
                    event = json.loads(line.decode("utf-8"))
                    # Error/event handling
                    if "error" in event:
                        errors.append(event["error"])
                        continue
                    # Tool/function-calling handling
                    if "toolCalls" in event:
                        tool_calls.extend(event["toolCalls"])
                    # ADK-style response: extract text from 'content.parts[0].text'
                    if "content" in event:
                        content = event["content"]
                        if "parts" in content and isinstance(content["parts"], list) and content["parts"]:
                            part = content["parts"][0]
                            if "text" in part:
                                texts.append(part["text"])
                except Exception as ex:
                    errors.append(f"Parse error: {ex}")
                    continue
        result = {}
        if texts:
            result["text"] = "\n".join(texts)
        if tool_calls:
            result["tool_calls"] = tool_calls
        if errors:
            result["errors"] = errors
        return result

    # Try :streamQuery first
    stream_url = base + ":streamQuery"
    stream_resp = requests.post(stream_url, headers=headers, data=json.dumps(payload), stream=True)
    if stream_resp.status_code == 404:
        # Fallback to :query
        query_url = base + ":query"
        query_resp = requests.post(query_url, headers=headers, data=json.dumps(payload))
        try:
            query_resp.raise_for_status()
        except Exception:
            print("REST API error (:query):", query_resp.text)
            raise
        # For :query, expect a single JSON response
        result = query_resp.json()
        out = {}
        # Extract errors
        if "error" in result:
            out["errors"] = [result["error"]]
        # Tool/function-calling
        if "toolCalls" in result:
            out["tool_calls"] = result["toolCalls"]
        if "response" in result:
            resp = result["response"]
            if "text" in resp:
                out["text"] = resp["text"]
            elif "parts" in resp:
                texts = [p.get("text", "") for p in resp["parts"] if "text" in p]
                out["text"] = "\n".join(texts)
            if "toolCalls" in resp:
                out.setdefault("tool_calls", []).extend(resp["toolCalls"])
        elif "outputs" in result and result["outputs"]:
            out["text"] = str(result["outputs"][0])
        if not out:
            out["raw"] = str(result)
        return out
    else:
        try:
            stream_resp.raise_for_status()
        except Exception:
            print("REST API error (:streamQuery):", stream_resp.text)
            raise
        # For :streamQuery, parse streaming NDJSON
        return parse_streaming_response(stream_resp)


    # Try to extract the response text
    if "response" in result:
        parts = result["response"].get("parts", [])
        texts = [p.get("text", "") for p in parts if "text" in p]
        return "\n".join(texts)
    elif "outputs" in result and result["outputs"]:
        return str(result["outputs"][0])
    elif "events" in result and result["events"]:
        for evt in result["events"]:
            if "response" in evt and "parts" in evt["response"]:
                texts = [p.get("text", "") for p in evt["response"]["parts"] if "text" in p]
                return "\n".join(texts)
    return str(result)
