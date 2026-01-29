from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Set, List
import re


class ConversationState(Enum):
    GREETING = "greeting"
    SUPPORT_FLOW = "support_flow"
    SALES_FLOW = "sales_flow"
    ERROR_HANDLING = "error_handling"


class InquiryType(Enum):
    SUPPORT = "support"
    SALES = "sales"
    GENERAL = "general"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        return [inquiry_type.value for inquiry_type in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.get_all_values()
    
    @classmethod
    def from_string(cls, value: str) -> 'InquiryType':
        for inquiry_type in cls:
            if inquiry_type.value == value:
                return inquiry_type
        raise ValueError(f"Invalid inquiry type: {value}")



@dataclass
class Message:
    """
    Represents a single message in the conversation.
    
    Attributes:
        role: Either 'user' or 'agent'
        content: The message text content
        timestamp: When the message was created
        metadata: Additional message metadata
    """
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        if not isinstance(self.role, str):
            raise ValueError("Role must be a string")
        
        if self.role not in ['user', 'agent']:
            raise ValueError("Role must be either 'user' or 'agent'")
        
        if not isinstance(self.content, str):
            raise ValueError("Content must be a string")
        
        if not self.content.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")


@dataclass
class UserInfo:
    """
    Stores collected user information during the conversation.
    
    Attributes:
        name: User's name
        policy_number: Insurance policy number
        contact_info: Contact information (email/phone)
        inquiry_type: Type of inquiry (support/sales)
        collected_fields: Set of fields that have been collected
    """
    name: Optional[str] = None
    policy_number: Optional[str] = None
    contact_info: Optional[str] = None
    inquiry_type: Optional[str] = None
    collected_fields: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        # Validate name if provided
        if self.name is not None:
            if not isinstance(self.name, str):
                raise ValueError("Name must be a string")
            if not self.name.strip():
                raise ValueError("Name cannot be empty or whitespace only")
        
        # Validate policy number if provided
        if self.policy_number is not None:
            if not isinstance(self.policy_number, str):
                raise ValueError("Policy number must be a string")
            if not self.policy_number.strip():
                raise ValueError("Policy number cannot be empty or whitespace only")
        
        # Validate contact info if provided
        if self.contact_info is not None:
            if not isinstance(self.contact_info, str):
                raise ValueError("Contact info must be a string")
            if not self.contact_info.strip():
                raise ValueError("Contact info cannot be empty or whitespace only")
        
        # Validate inquiry type if provided
        if self.inquiry_type is not None:
            if not isinstance(self.inquiry_type, str):
                raise ValueError("Inquiry type must be a string")
            if not InquiryType.is_valid(self.inquiry_type):
                valid_types = InquiryType.get_all_values()
                raise ValueError(f"Inquiry type must be one of: {valid_types}")
        
        # Validate collected fields
        if not isinstance(self.collected_fields, set):
            raise ValueError("Collected fields must be a set")
        
        valid_fields = UserInfo.get_valid_fields()
        invalid_fields = self.collected_fields - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid collected fields: {invalid_fields}")
    
    def add_field(self, field_name: str, value: str) -> None:
        valid_fields = UserInfo.get_valid_fields()
        if field_name not in valid_fields:
            raise ValueError(f"Invalid field name: {field_name}. Valid fields: {valid_fields}")
        
        setattr(self, field_name, value)
        self.collected_fields.add(field_name)
        self.validate()
    
    def has_field(self, field_name: str) -> bool:
        return field_name in self.collected_fields
    
    def get_completion_percentage(self) -> float:
        total_fields = len(UserInfo.get_valid_fields())
        return len(self.collected_fields) / total_fields
    
    @classmethod
    def get_valid_fields(cls) -> Set[str]:
        return {field.name for field in dataclasses.fields(cls) if field.name != 'collected_fields'}


@dataclass
class SessionStats:
    """
    Tracks statistics about the current conversation session.
    
    Attributes:
        message_count: Total number of messages in the conversation
        conversation_duration: How long the conversation has been active
        user_info_collected: User information gathered during the session
        current_state: Current conversation state
        last_activity: Timestamp of last user activity
    """
    message_count: int = 0
    conversation_duration: timedelta = field(default_factory=lambda: timedelta(0))
    user_info_collected: UserInfo = field(default_factory=UserInfo)
    current_state: str = ConversationState.GREETING.value
    last_activity: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        if not isinstance(self.message_count, int):
            raise ValueError("Message count must be an integer")
        
        if self.message_count < 0:
            raise ValueError("Message count cannot be negative")
        
        if not isinstance(self.conversation_duration, timedelta):
            raise ValueError("Conversation duration must be a timedelta object")
        
        if self.conversation_duration.total_seconds() < 0:
            raise ValueError("Conversation duration cannot be negative")
        
        if not isinstance(self.user_info_collected, UserInfo):
            raise ValueError("User info collected must be a UserInfo object")
        
        if not isinstance(self.current_state, str):
            raise ValueError("Current state must be a string")
        
        valid_states = [state.value for state in ConversationState]
        if self.current_state not in valid_states:
            raise ValueError(f"Current state must be one of: {valid_states}")
        
        if not isinstance(self.last_activity, datetime):
            raise ValueError("Last activity must be a datetime object")
    
    def increment_message_count(self) -> None:
        self.message_count += 1
        self.last_activity = datetime.now()
        self.validate()
    
    def update_state(self, new_state: ConversationState) -> None:
        self.current_state = new_state.value
        self.last_activity = datetime.now()
        self.validate()
    
    def update_duration(self, start_time: datetime) -> None:
        self.conversation_duration = datetime.now() - start_time
        self.validate()
    
    def reset(self) -> None:
        """Reset all statistics to initial values."""
        self.message_count = 0
        self.conversation_duration = timedelta(0)
        self.user_info_collected = UserInfo()
        self.current_state = ConversationState.GREETING.value
        self.last_activity = datetime.now()
        self.validate()