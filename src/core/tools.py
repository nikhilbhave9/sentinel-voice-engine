"""
Mock Toolset for Sentinel Insurance Agent.
These functions simulate backend API calls for policy lookups and scheduling.
"""
from typing import Dict, List, Any

def lookup_policy(policy_number: str, operation: str = "lookup") -> Dict[str, Any]:
    """
    Retrieves policy details or indicates if escalation is needed.
    
    Args:
        policy_number: The policy number to look up
        operation: The operation type (lookup, change_address, claim_status, update_beneficiary)
    
    Returns:
        Structured response with escalation indicator:
        {
            "status": str,  # "success", "not_supported", "error"
            "action": str,  # "continue", "escalate", "retry"
            "escalation_required": bool,
            "data": Any,  # Tool-specific response data
            "message": str  # Human-readable message
        }
    """
    # Unsupported operations that require human intervention
    unsupported_operations = [
        "change_address", "update_address", "address_change",
        "claim_status", "check_claim", "claim_inquiry",
        "update_beneficiary", "change_beneficiary", "beneficiary_update"
    ]
    
    # Check if operation requires escalation
    if operation.lower() in unsupported_operations:
        return {
            "status": "not_supported",
            "action": "escalate",
            "escalation_required": True,
            "data": None,
            "message": f"Operation '{operation}' requires specialist assistance"
        }
    
    # Standard policy lookup
    mock_db = {
        "POL123": {
            "status": "Active",
            "type": "Auto",
            "coverage": "Full Comprehensive",
            "holder": "John"
        },
        "FIRE99": {
            "status": "Active",
            "type": "Fire/Home",
            "coverage": "Structure & Contents",
            "holder": "Jane"
        }
    }
    
    policy_data = mock_db.get(policy_number.upper())
    
    if policy_data:
        return {
            "status": "success",
            "action": "continue",
            "escalation_required": False,
            "data": policy_data,
            "message": f"Policy {policy_number}: Status: {policy_data['status']}, Type: {policy_data['type']}, Coverage: {policy_data['coverage']}, Holder: {policy_data['holder']}"
        }
    else:
        return {
            "status": "error",
            "action": "retry",
            "escalation_required": False,
            "data": None,
            "message": "Error: Policy number not found."
        }

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