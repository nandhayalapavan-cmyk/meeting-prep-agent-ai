"""
Meeting Prep Agent (built on Hindsight)

Remembers past meetings with each contact: what was discussed, what was promised,
which follow-ups were missed. Learns your meeting style and preparation preferences.
Briefs you with full context from every past interaction with a contact.
"""
import argparse
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "meeting-prep-agent")
client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888"),
    api_key=os.getenv("HINDSIGHT_API_KEY") or None,
)

MISSION = (
    "I am a meeting preparation assistant. I remember every past meeting with each "
    "contact: what was discussed, what was promised (by either side), and which "
    "follow-ups were missed. I also learn the user's meeting style and preparation "
    "preferences, and use them to shape every briefing."
)


def setup():
    """Create the memory bank (safe to run repeatedly)."""
    try:
        client.create_bank(bank_id=BANK_ID, name="Meeting Prep Agent", mission=MISSION)
        print(f"Bank '{BANK_ID}' ready.")
    except Exception as e:  # bank may already exist
        print(f"Bank setup note: {e}")


def log_meeting(contact, discussed, promised_by_me="", promised_by_them="",
                followups_missed="", date=None):
    """Store a meeting so it can be recalled later."""
    when = date or datetime.now(timezone.utc).date().isoformat()
    parts = [f"Meeting with {contact} on {when}.", f"Discussed: {discussed}."]
    if promised_by_me:
        parts.append(f"I promised {contact}: {promised_by_me}.")
    if promised_by_them:
        parts.append(f"{contact} promised me: {promised_by_them}.")
    if followups_missed:
        parts.append(f"Missed follow-ups with {contact}: {followups_missed}.")
    client.retain(
        bank_id=BANK_ID,
        content=" ".join(parts),
        context=f"meeting with {contact}",
        timestamp=f"{when}T09:00:00Z",
    )
    print(f"Saved meeting with {contact}.")


def save_preference(text):
    """Teach the agent your meeting style / prep preferences."""
    client.retain(bank_id=BANK_ID, content=f"My meeting preference: {text}",
                  context="user meeting style and preparation preferences")
    print("Preference saved.")


def brief(contact):
    """Full-context briefing for an upcoming meeting."""
    query = (
        f"I have an upcoming meeting with {contact}. Give me a briefing covering: "
        f"1) what we discussed in every past meeting, 2) what I promised them and "
        f"what they promised me, 3) follow-ups that were missed or are still open, "
        f"4) suggested talking points. Format it following my meeting style and "
        f"preparation preferences."
    )
    print(client.reflect(bank_id=BANK_ID, query=query).text)


def open_followups(contact):
    """Just the missed / outstanding follow-ups."""
    query = (f"List every promise and follow-up involving {contact} that was missed "
             f"or is still outstanding, and who owes it.")
    print(client.reflect(bank_id=BANK_ID, query=query).text)


def history(contact):
    """Raw recalled memories for a contact."""
    for r in client.recall(bank_id=BANK_ID, query=f"meetings with {contact}").results:
        print(f"- {r.text}")


def main():
    p = argparse.ArgumentParser(description="Meeting Prep Agent (Hindsight)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup")

    m = sub.add_parser("log", help="record a past meeting")
    m.add_argument("contact")
    m.add_argument("--discussed", required=True)
    m.add_argument("--i-promised", default="")
    m.add_argument("--they-promised", default="")
    m.add_argument("--missed", default="")
    m.add_argument("--date", default=None, help="YYYY-MM-DD")

    pr = sub.add_parser("pref", help="teach a meeting/prep preference")
    pr.add_argument("text")

    for name in ("brief", "followups", "history"):
        s = sub.add_parser(name)
        s.add_argument("contact")

    a = p.parse_args()
    if a.cmd == "setup":
        setup()
    elif a.cmd == "log":
        log_meeting(a.contact, a.discussed, a.i_promised, a.they_promised, a.missed, a.date)
    elif a.cmd == "pref":
        save_preference(a.text)
    elif a.cmd == "brief":
        brief(a.contact)
    elif a.cmd == "followups":
        open_followups(a.contact)
    elif a.cmd == "history":
        history(a.contact)


if __name__ == "__main__":
    main()
