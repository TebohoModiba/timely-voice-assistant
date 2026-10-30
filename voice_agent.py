"""Time-management voice buddy: reminders, habit tracking and a daily log."""

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.DEBUG)

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from strands import tool
from strands.bidi.agent import BidiAgent
from strands.bidi.io import AudioIO
from strands.bidi.models import BedrockNovaSonicModel

AGENT_NAME = "Timely"  # change this to rename the agent
DATA_FILE = Path(__file__).parent / "tracker_data.json"

SYSTEM_PROMPT = f"""You are {AGENT_NAME}, a warm, friendly voice assistant that
helps people manage their time, remember tasks and keep a record of their day.

You can: set and list reminders, mark them done, record habits the user
mentions (like exercise, reading or drinking water), summarise habits, and
keep a daily log of what the user did.

Rules:
- Keep every spoken reply to one or two short sentences. This is a voice chat.
- Before setting a reminder, call get_current_time so you can turn words like
  "in 30 minutes" or "tomorrow at 9" into an exact date and time.
- When the user mentions doing a habit or finishing something, record it with
  the right tool without making them ask twice, then briefly confirm.
- If a time is unclear, ask one short question.
- Be encouraging, never judgemental, about missed habits.
- If you receive a message saying a reminder is due now, tell the user about
  it right away in one friendly sentence.
- If the user says goodbye, say goodbye warmly."""


# ---------- storage helpers ----------
def _load() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"reminders": [], "habits": [], "log": []}


def _save(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------- tools the voice model can call ----------
@tool
def get_current_time() -> str:
    """Get the current local date, time and weekday."""
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M")


@tool
def add_reminder(task: str, due: str) -> str:
    """Set a reminder.

    Args:
        task: What the user wants to be reminded about.
        due: When it is due, as local time in the format YYYY-MM-DD HH:MM.
    """
    try:
        datetime.strptime(due, "%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid time. Use the format YYYY-MM-DD HH:MM."
    data = _load()
    data["reminders"].append(
        {"task": task, "due": due, "done": False, "notified": False}
    )
    _save(data)
    return f"Reminder set: {task} at {due}."


@tool
def list_reminders() -> str:
    """List the user's reminders that are not done yet."""
    pending = [r for r in _load()["reminders"] if not r["done"]]
    if not pending:
        return "No pending reminders."
    pending.sort(key=lambda r: r["due"])
    return "; ".join(f"{r['task']} at {r['due']}" for r in pending)


@tool
def complete_reminder(task: str) -> str:
    """Mark a reminder as done.

    Args:
        task: Words from the reminder, e.g. 'bank'.
    """
    data = _load()
    for r in data["reminders"]:
        if not r["done"] and task.lower() in r["task"].lower():
            r["done"] = True
            _save(data)
            return f"Marked done: {r['task']}."
    return "I couldn't find a matching reminder."


@tool
def log_habit(habit: str, note: str = "") -> str:
    """Record that the user did a habit today.

    Args:
        habit: The habit, e.g. 'exercise', 'reading', 'drank water'.
        note: Optional detail such as '30 minutes'.
    """
    data = _load()
    data["habits"].append(
        {"habit": habit.lower(), "date": _today(), "note": note}
    )
    _save(data)
    return f"Logged habit: {habit} for today."


@tool
def habit_summary(habit: str = "", days: int = 7) -> str:
    """Summarise how often habits were done recently.

    Args:
        habit: A specific habit, or empty for all habits.
        days: How many days back to look.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    counts: dict[str, set] = {}
    for h in _load()["habits"]:
        if h["date"] >= cutoff and (not habit or habit.lower() in h["habit"]):
            counts.setdefault(h["habit"], set()).add(h["date"])
    if not counts:
        return f"No habits logged in the last {days} days."
    return "; ".join(
        f"{name}: {len(d)} of {days} days" for name, d in counts.items()
    )


@tool
def add_log_entry(entry: str) -> str:
    """Add something the user did to today's daily log.

    Args:
        entry: What the user did, in a short sentence.
    """
    data = _load()
    data["log"].append(
        {"date": _today(), "time": datetime.now().strftime("%H:%M"), "entry": entry}
    )
    _save(data)
    return "Added to today's log."


@tool
def get_daily_log(date: str = "") -> str:
    """Read the daily log for a day.

    Args:
        date: Day as YYYY-MM-DD. Leave empty for today.
    """
    day = date or _today()
    entries = [e for e in _load()["log"] if e["date"] == day]
    habits = [h for h in _load()["habits"] if h["date"] == day]
    if not entries and not habits:
        return f"Nothing logged for {day}."
    parts = [f"{e['time']} {e['entry']}" for e in entries]
    parts += [f"habit: {h['habit']}" for h in habits]
    return f"{day}: " + "; ".join(parts)


# ---------- background reminder check ----------
async def reminder_watcher(agent: BidiAgent) -> None:
    """Every 20 seconds, announce any reminders that have come due."""
    while True:
        await asyncio.sleep(20)
        data = _load()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        changed = False
        for r in data["reminders"]:
            if not r["done"] and not r["notified"] and r["due"] <= now:
                r["notified"] = True
                changed = True
                print(f"\n*** REMINDER: {r['task']} ***\n")
                try:
                    await agent.send(
                        f"Reminder is due now: {r['task']}. "
                        "Tell the user in one friendly sentence."
                    )
                except Exception as exc:
                    print(f"(could not speak reminder: {exc})")
        if changed:
            _save(data)


async def main() -> None:
    model = BedrockNovaSonicModel(
        model_id="amazon.nova-2-5-sonic",
        region="eu-north-1",
        voice="tiffany",
    )
    agent = BidiAgent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_current_time, add_reminder, list_reminders, complete_reminder,
            log_habit, habit_summary, add_log_entry, get_daily_log,
        ],
    )
    audio = AudioIO(audio_processor=True)  # echo cancellation

    print(f"{AGENT_NAME} is listening. Start talking. Press Ctrl+C to end.\n")
    watcher = asyncio.create_task(reminder_watcher(agent))
    try:
        await agent.run(inputs=[audio.input()], outputs=[audio.output()])
    finally:
        watcher.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nConversation ended. Goodbye!")