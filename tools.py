"""
The tools our agent is allowed to use.

Each tool has two halves:
  1. A DECLARATION (name, description, parameters) that we send to the model,
     so it knows the tool exists and how to call it.
  2. A plain Python FUNCTION that OUR code runs when the model asks for it.

The model never runs these functions itself. It only asks.
"""
from datetime import date


def get_current_date() -> dict:
    """Return today's date. The model can't know this on its own."""
    return {"today": date.today().isoformat()}


def days_between(start_date: str, end_date: str) -> dict:
    """Days from start_date to end_date (YYYY-MM-DD). Negative if end is earlier."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    return {"days": (end - start).days}

def day_of_week(date_str: str) -> dict:
    """Returns the weekday for a given date."""
    d = date.fromisoformat(date_str)
    return {"week": d.weekday()}

TOOL_DECLARATIONS = [
    {
        "name": "get_current_date",
        "description": "Returns today's date in YYYY-MM-DD format. "
                       "Call this whenever the answer depends on today's date.",
    },
    {
        "name": "days_between",
        "description": "Counts the number of days from start_date to end_date.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date, YYYY-MM-DD."},
                "end_date": {"type": "string", "description": "End date, YYYY-MM-DD."},
            },
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "day_of_week",
        "description": "Returns the weekday for a given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "Date, YYYY-MM-DD."},
            },
            "required": ["date_str"],
        },
    }
]

# The allowlist: the ONLY functions the agent can trigger.
TOOL_FUNCTIONS = {
    "get_current_date": get_current_date,
    "days_between": days_between,
    "day_of_week": day_of_week,
}
