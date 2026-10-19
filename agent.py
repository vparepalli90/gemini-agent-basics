"""
A minimal tool-calling agent, written by hand so every step of the loop is visible.

    question -> model -> (tool call? -> OUR code runs it -> result back to model) -> ... -> answer

Run:  python agent.py "How many days until New Year's Day 2027?"
"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_STEPS = 6  # hard cap on model calls: bounds cost and latency, stops runaway loops

SYSTEM_PROMPT = (
    "You are a precise assistant. Use the tools for anything involving today's date "
    "or counting days or print what day it is. Never guess today's date. Keep final answers short."
)


def run_tool(call: types.FunctionCall) -> dict:
    """Guardrail layer: only allowlisted tools run, and bad arguments never crash the agent."""
    func = TOOL_FUNCTIONS.get(call.name)
    if func is None:
        return {"error": f"Unknown tool '{call.name}'. Available: {sorted(TOOL_FUNCTIONS)}"}
    try:
        return func(**(call.args or {}))
    except Exception as exc:  # e.g. a badly formatted date from the model
        return {"error": f"{type(exc).__name__}: {exc}"}


def run_agent(question: str, client, max_steps: int = MAX_STEPS, verbose: bool = True) -> str:
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
        # We run the loop ourselves, so the SDK must not call tools automatically.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    # The conversation so far: this list IS the agent's short-term memory.
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]

    for step in range(1, max_steps + 1):
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        if not response.candidates:
            return "Stopped: the model returned no answer."

        model_turn = response.candidates[0].content
        calls = [p.function_call for p in (model_turn.parts or []) if p.function_call]

        # Stopping condition: no tool requested means this is the final answer.
        if not calls:
            return response.text or ""

        contents.append(model_turn)  # remember what the model asked for
        result_parts = []
        for call in calls:
            result = run_tool(call)  # OUR code executes the tool
            if verbose:
                print(f"[step {step}] {call.name}({dict(call.args or {})}) -> {result}")
            result_parts.append(types.Part(function_response=types.FunctionResponse(
                id=call.id, name=call.name, response={"result": result},
            )))
        contents.append(types.Content(role="user", parts=result_parts))  # feed results back

    return f"Stopped: reached the limit of {max_steps} steps without a final answer."


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Missing GEMINI_API_KEY. Copy .env.example to .env and add your key.")
    question = " ".join(sys.argv[1:]) or "How many days are left until New Year's Day 2027?"
    client = genai.Client(api_key=api_key)
    print(f"Q: {question}\n")
    print(f"\nA: {run_agent(question, client)}")


if __name__ == "__main__":
    main()
