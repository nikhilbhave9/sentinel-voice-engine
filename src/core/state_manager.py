import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from .models import Message, UserInfo, SessionStats, ConversationState


class SessionKeys(Enum):
    """Enumeration of session state keys for Streamlit state management."""
    MESSAGES = 'messages'
    CONVERSATION_STATE = 'conversation_state'
    MESSAGE_COUNT = 'message_count'
    USER_INFO = 'user_info'
    SESSION_START_TIME = 'session_start_time'
    INITIALIZED = 'initialized'


class StateManager:
    """
    Manages all application state using Streamlit's session state.
    
    This class provides a centralized interface for managing conversation data,
    user information, and session statistics with persistence across Streamlit reruns.
    """
    
    def __init__(self):
        self.initialize_state()
    
    def initialize_state(self) -> None:
        if not st.session_state.get(SessionKeys.INITIALIZED.value, False):
            # Initialize conversation messages
            st.session_state[SessionKeys.MESSAGES.value] = []
            
            # Initialize conversation state
            st.session_state[SessionKeys.CONVERSATION_STATE.value] = ConversationState.GREETING.value
            
            # Initialize message count
            st.session_state[SessionKeys.MESSAGE_COUNT.value] = 0
            
            # Initialize user info
            st.session_state[SessionKeys.USER_INFO.value] = UserInfo()
            
            # Initialize session start time
            st.session_state[SessionKeys.SESSION_START_TIME.value] = datetime.now()
            
            # Mark as initialized
            st.session_state[SessionKeys.INITIALIZED.value] = True
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if metadata is None:
            metadata = {}
        
        # Create and validate the message
        message = Message(role=role, content=content, metadata=metadata)
        
        # Add to session state
        messages = st.session_state.get(SessionKeys.MESSAGES.value, [])
        messages.append({
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'metadata': message.metadata
        })
        st.session_state[SessionKeys.MESSAGES.value] = messages
        
        # Update message count
        st.session_state[SessionKeys.MESSAGE_COUNT.value] = len(messages)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        return st.session_state.get(SessionKeys.MESSAGES.value, [])
    
    def get_message_count(self) -> int:
        return st.session_state.get(SessionKeys.MESSAGE_COUNT.value, 0)
    
    def update_conversation_state(self, new_state: ConversationState) -> None:
        if not isinstance(new_state, ConversationState):
            raise ValueError("new_state must be a ConversationState enum value")
        
        st.session_state[SessionKeys.CONVERSATION_STATE.value] = new_state.value
    
    def get_conversation_state(self) -> str:
        return st.session_state.get(SessionKeys.CONVERSATION_STATE.value, ConversationState.GREETING.value)
    
    def update_user_info(self, field_name: str, value: str) -> None:
        # Get current user info or create new one
        user_info_data = st.session_state.get(SessionKeys.USER_INFO.value)
        if isinstance(user_info_data, dict):
            # Convert dict to UserInfo object
            user_info = UserInfo(
                name=user_info_data.get('name'),
                policy_number=user_info_data.get('policy_number'),
                contact_info=user_info_data.get('contact_info'),
                inquiry_type=user_info_data.get('inquiry_type'),
                collected_fields=set(user_info_data.get('collected_fields', []))
            )
        elif isinstance(user_info_data, UserInfo):
            user_info = user_info_data
        else:
            user_info = UserInfo()
        
        # Update the field
        user_info.add_field(field_name, value)
        
        # Store back in session state as dict for JSON serialization
        st.session_state[SessionKeys.USER_INFO.value] = {
            'name': user_info.name,
            'policy_number': user_info.policy_number,
            'contact_info': user_info.contact_info,
            'inquiry_type': user_info.inquiry_type,
            'collected_fields': list(user_info.collected_fields)
        }
    
    def get_user_info(self) -> UserInfo:
        user_info_data = st.session_state.get(SessionKeys.USER_INFO.value)
        
        if isinstance(user_info_data, dict):
            return UserInfo(
                name=user_info_data.get('name'),
                policy_number=user_info_data.get('policy_number'),
                contact_info=user_info_data.get('contact_info'),
                inquiry_type=user_info_data.get('inquiry_type'),
                collected_fields=set(user_info_data.get('collected_fields', []))
            )
        elif isinstance(user_info_data, UserInfo):
            return user_info_data
        else:
            return UserInfo()
    
    def get_session_stats(self) -> SessionStats:
        # Calculate conversation duration
        start_time = st.session_state.get(SessionKeys.SESSION_START_TIME.value, datetime.now())
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        duration = datetime.now() - start_time
        
        # Get user info
        user_info = self.get_user_info()
        
        # Get current state
        current_state = self.get_conversation_state()
        
        # Get message count
        message_count = self.get_message_count()
        
        # Create and return session stats
        return SessionStats(
            message_count=message_count,
            conversation_duration=duration,
            user_info_collected=user_info,
            current_state=current_state,
            last_activity=datetime.now()
        )
    
    def clear_conversation(self) -> None:
        # Clear conversation messages
        st.session_state[SessionKeys.MESSAGES.value] = []
        
        # Reset conversation state
        st.session_state[SessionKeys.CONVERSATION_STATE.value] = ConversationState.GREETING.value
        
        # Reset message count
        st.session_state[SessionKeys.MESSAGE_COUNT.value] = 0
        
        # Reset user info
        st.session_state[SessionKeys.USER_INFO.value] = UserInfo()
        
        # Reset session start time
        st.session_state[SessionKeys.SESSION_START_TIME.value] = datetime.now()
        
        # Keep initialized flag as True
        st.session_state[SessionKeys.INITIALIZED.value] = True
    
    def is_initialized(self) -> bool:
        return st.session_state.get(SessionKeys.INITIALIZED.value, False)
    
    def get_session_start_time(self) -> datetime:
        start_time = st.session_state.get(SessionKeys.SESSION_START_TIME.value, datetime.now())
        if isinstance(start_time, str):
            return datetime.fromisoformat(start_time)
        return start_time
    
    def export_state(self) -> Dict[str, Any]:
        return {
            'messages': self.get_messages(),
            'conversation_state': self.get_conversation_state(),
            'message_count': self.get_message_count(),
            'user_info': st.session_state.get(SessionKeys.USER_INFO.value),
            'session_start_time': st.session_state.get(SessionKeys.SESSION_START_TIME.value),
            'initialized': self.is_initialized()
        }
    
    def convert_messages_for_gemini(self) -> List[Dict[str, str]]:
        messages = self.get_messages()
        gemini_messages = []
        
        for msg in messages:
            role = msg['role']
            # Convert 'agent' to 'model' for Gemini API
            if role == 'agent':
                role = 'model'
            
            gemini_messages.append({
                'role': role,
                'content': msg['content']
            })
        
        return gemini_messages