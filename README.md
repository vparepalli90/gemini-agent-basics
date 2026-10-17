# Gemini Agent Basics

A minimal tool-calling agent built **by hand** with the Gemini API (`google-genai`), so every step of the agent loop is visible instead of hidden inside a framework.

## How it works

```
question ─► model ─► wants a tool? ── no ──► final answer
              ▲            │ yes
              │            ▼
              └── result ◄─ my code runs the tool (allowlisted, validated)
```

1. The model gets the question plus **tool declarations** (name, description, parameters).
2. If it needs a tool, it replies with a structured **function call**. It never runs code itself.
3. **My code** runs the tool and sends the result back.
4. Repeat until the model answers, or until `MAX_STEPS` stops it.

## Guardrails

| Risk | How it's handled |
|---|---|
| Model asks for a tool that doesn't exist | Allowlist (`TOOL_FUNCTIONS`): unknown tools are refused and the model is told so |
| Model passes bad arguments | Tool errors are caught and returned to the model as messages, never a crash |
| Agent loops forever | `MAX_STEPS` caps model calls, bounding cost and latency |
| API key leaks | Key lives in `.env`, which is gitignored |

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env        # then paste your key into .env  (Windows: copy .env.example .env)
python test_agent.py        # tests the loop offline with a fake model, no key needed
python agent.py "How many days are left until New Year's Day 2027?"
```

## What I learned

- An agent is a loop with a stopping condition; the model chooses the next step.
- Tool calling is a request, not execution: security lives in the code that runs tools.
- Testing an agent doesn't require the real model: a fake client makes the loop testable.
