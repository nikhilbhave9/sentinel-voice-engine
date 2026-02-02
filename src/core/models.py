"""
Core data models for the insurance agent application.
Preserved from the original system to maintain domain logic.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ConversationState(Enum):
    """Enumeration of conversation states"""
    GREETING = "greeting"
    SUPPORT_FLOW = "support_flow"
    SALES_FLOW = "sales_flow"
    ERROR_HANDLING = "error_handling"


@dataclass
class UserInfo:
    """User information collected during conversations"""
    name: Optional[str] = None
    policy_number: Optional[str] = None
    contact_info: Optional[str] = None
    inquiry_type: Optional[str] = None

    def get_valid_fields(self) -> List[str]:
        """Return list of valid field names for validation"""
        return ['name', 'policy_number', 'contact_info', 'inquiry_type']

    def is_complete(self) -> bool:
        """Check if all required user information is collected"""
        return all([self.name, self.contact_info, self.inquiry_type])

    def get_collected_fields(self) -> List[str]:
        """Return list of fields that have been collected"""
        collected = []
        if self.name:
            collected.append('name')
        if self.policy_number:
            collected.append('policy_number')
        if self.contact_info:
            collected.append('contact_info')
        if self.inquiry_type:
            collected.append('inquiry_type')
        return collected


@dataclass
class ConversationStateData:
    """Current state of the conversation (dataclass version for simplified system)"""
    current_state: str = "greeting"
    user_info: UserInfo = field(default_factory=UserInfo)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def is_valid_state(self, state: str) -> bool:
        """Validate if the given state is valid"""
        valid_states = ["greeting", "support_flow", "sales_flow", "error_handling"]
        return state in valid_states

    def add_message(self, role: str, content: str, source: str = "text") -> None:
        """Add a message to conversation history
        
        Args:
            role: The role of the message sender (user/assistant)
            content: The message content
            source: The source of the message (voice/text), defaults to "text"
        """
        self.conversation_history.append({
            'role': role,
            'content': content,
            'source': source,
            'timestamp': str(Dict[str, Any])  # Placeholder for timestamp
        })


# Additional models for session management
@dataclass
class Message:
    """Individual message in conversation"""
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class SessionStats:
    """Session statistics for monitoring"""
    message_count: int = 0
    conversation_duration: Any = None  # timedelta object
    user_info_collected: UserInfo = field(default_factory=UserInfo)
    current_state: str = "greeting"
    session_start_time: Any = None  # datetime object
    last_activity: Any = None  # datetime object