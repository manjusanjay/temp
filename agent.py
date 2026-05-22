import random
import string
from datetime import datetime

# Simulated ticket database (in memory for demo)
tickets_db = {}

def generate_ticket_id():
    return "TKT-" + ''.join(random.choices(string.digits, k=6))

def create_ticket(issue_summary: str, priority: str, user_name: str = "Demo User") -> dict:
    """
    Agent Tool 1: Creates a support ticket in the system
    """
    ticket_id = generate_ticket_id()
    ticket = {
        "ticket_id": ticket_id,
        "summary": issue_summary,
        "priority": priority,
        "status": "Open",
        "created_by": user_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "assigned_to": "IT Helpdesk Team"
    }
    tickets_db[ticket_id] = ticket
    return ticket

def check_ticket_status(ticket_id: str) -> dict:
    """
    Agent Tool 2: Checks status of an existing ticket
    """
    if ticket_id in tickets_db:
        return tickets_db[ticket_id]
    else:
        return {"error": f"Ticket {ticket_id} not found"}

def escalate_ticket(ticket_id: str, reason: str) -> dict:
    """
    Agent Tool 3: Escalates a ticket to senior IT team
    """
    if ticket_id in tickets_db:
        tickets_db[ticket_id]["status"] = "Escalated"
        tickets_db[ticket_id]["assigned_to"] = "Senior IT Engineer"
        tickets_db[ticket_id]["escalation_reason"] = reason
        tickets_db[ticket_id]["escalated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return tickets_db[ticket_id]
    else:
        return {"error": f"Ticket {ticket_id} not found"}

# Tool definitions to pass to Gemini
TOOLS = [
    {
        "name": "create_ticket",
        "description": "Creates a new IT support ticket when the user has an issue that needs to be tracked or resolved by the IT team.",
        "parameters": {
            "issue_summary": "A brief summary of the issue",
            "priority": "Priority level: P1, P2, P3, or P4"
        }
    },
    {
        "name": "check_ticket_status",
        "description": "Checks the current status of an existing support ticket using the ticket ID.",
        "parameters": {
            "ticket_id": "The ticket ID in format TKT-XXXXXX"
        }
    },
    {
        "name": "escalate_ticket",
        "description": "Escalates an existing ticket to the senior IT team when the issue is critical or unresolved for too long.",
        "parameters": {
            "ticket_id": "The ticket ID to escalate",
            "reason": "Reason for escalation"
        }
    }
]

def execute_tool(tool_name: str, parameters: dict) -> dict:
    """Execute the requested tool and return result"""
    if tool_name == "create_ticket":
        return create_ticket(
            issue_summary=parameters.get("issue_summary", "Unknown issue"),
            priority=parameters.get("priority", "P3")
        )
    elif tool_name == "check_ticket_status":
        return check_ticket_status(parameters.get("ticket_id", ""))
    elif tool_name == "escalate_ticket":
        return escalate_ticket(
            ticket_id=parameters.get("ticket_id", ""),
            reason=parameters.get("reason", "User requested escalation")
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}
