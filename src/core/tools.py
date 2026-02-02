"""
Mock Toolset for Sentinel Insurance Agent.
These functions simulate backend API calls for policy lookups and scheduling.
"""
from typing import Dict, List

def lookup_policy(policy_number: str) -> str:
    """
    Retrieves policy details. Use this when a user provides a policy number in the Support Flow.
    """
    mock_db = {
        "POL123": "Status: Active. Type: Auto. Coverage: Full Comprehensive. Holder: John.",
        "FIRE99": "Status: Active. Type: Fire/Home. Coverage: Structure & Contents. Holder: Jane.",
    }
    return mock_db.get(policy_number.upper(), "Error: Policy number not found.")

def triage_and_escalate(name: str, issue_description: str, phone: str) -> str:
    """
    Escalates complex issues to a human agent. Use this for claims or expired policies.
    """
    return f"SUCCESS: Handover triggered for {name}. Specialist will call {phone} regarding: {issue_description}."

def get_available_slots(insurance_type: str) -> List[str]:
    """
    Returns available appointment times for a sales consultation. Use this in the Sales Flow.
    """
    return ["Monday at 10:00 AM", "Tuesday at 2:00 PM", "Wednesday at 4:30 PM"]

def book_appointment(name: str, phone: str, time_slot: str) -> str:
    """
    Finalizes a sales appointment booking. Use this once name, phone, and slot are confirmed.
    """
    return f"CONFIRMED: Appointment for {name} ({phone}) at {time_slot} is booked."

# Dictionary for the Gemini SDK to map tool names to functions
SENTINEL_TOOL_MAP = {
    "lookup_policy": lookup_policy,
    "triage_and_escalate": triage_and_escalate,
    "get_available_slots": get_available_slots,
    "book_appointment": book_appointment
}