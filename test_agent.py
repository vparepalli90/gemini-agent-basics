"""
Tests the agent loop WITHOUT calling the real API, using a fake client that replays
scripted model replies. Run:  python test_agent.py
"""
from google.genai import types

from agent import run_agent
from tools import days_between
from tools import day_of_week


def call(name, args=None, call_id="1"):
    part = types.Part(function_call=types.FunctionCall(name=name, args=args or {}, id=call_id))
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[part]))])


def answer(text):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]))])


class FakeClient:
    """Stands in for genai.Client: returns scripted replies and records what it was sent."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.models = self

    def generate_content(self, model, contents, config):
        self.requests.append(list(contents))
        return self.replies.pop(0)


def tool_results(client):
    """Every function_response our code sent back to the model, in order."""
    last = client.requests[-1]
    return [p.function_response.response["result"]
            for c in last for p in (c.parts or []) if p.function_response]


# 1. Multi-step: the model needs today's date before it can count days.
client = FakeClient([
    call("get_current_date"),
    call("days_between", {"start_date": "2026-10-16", "end_date": "2027-01-01"}, "2"),
    answer("77 days."),
])
assert run_agent("Days until New Year?", client, verbose=False) == "77 days."
assert len(client.requests) == 3
assert tool_results(client)[-1] == {"days": 77}

# 2. Guardrail: an unknown tool is refused, not executed, and the agent keeps going.
client = FakeClient([call("delete_database"), answer("I can't do that.")])
assert run_agent("Drop everything", client, verbose=False) == "I can't do that."
assert "Unknown tool" in tool_results(client)[0]["error"]

# 3. Guardrail: bad arguments from the model become an error message, not a crash.
client = FakeClient([call("days_between", {"start_date": "next friday", "end_date": "2027-01-01"}),
                     answer("Please give a date as YYYY-MM-DD.")])
run_agent("Days from next friday?", client, verbose=False)
assert "ValueError" in tool_results(client)[0]["error"]

# 4. MAX_STEPS: a model that never stops is cut off.
client = FakeClient([call("get_current_date")] * 10)
result = run_agent("Loop forever", client, max_steps=3, verbose=False)
assert result.startswith("Stopped") and len(client.requests) == 3

# 5. The tool itself.
assert days_between("2026-10-16", "2027-01-01") == {"days": 77}
assert days_between("2027-01-01", "2026-10-16") == {"days": -77}


print("All agent tests passed.")
