# Requirements Document

## Introduction

Sentinel is an AI insurance voice agent designed to handle customer interactions through conversational interfaces. Stage 1 focuses on building a functional text-based conversational interface using Streamlit and Google Gemini LLM to establish the core conversational loop without voice components. This stage serves as the foundation for future voice integration and advanced insurance workflows.

## Glossary

- **Sentinel**: The AI insurance voice agent system
- **Chat_Interface**: The Streamlit-based user interface for text conversations
- **Conversation_State**: The current phase of interaction (greeting, support_flow, sales_flow, etc.)
- **Session_Statistics**: Metrics about the current conversation session
- **Gemini_LLM**: Google Gemini 1.5 Flash language model for AI responses
- **State_Manager**: Streamlit's state management system for persistence

## Requirements

### Requirement 1: Chat Interface Display

**User Story:** As a user, I want to see a clear chat interface, so that I can easily follow the conversation flow with the insurance agent.

#### Acceptance Criteria

1. THE Chat_Interface SHALL display conversation history in chat format with user messages on the right and agent messages on the left
2. THE Chat_Interface SHALL provide a text input box at the bottom of the screen for user message entry
3. THE Chat_Interface SHALL display the title "Sentinel Insurance Agent" prominently
4. THE Chat_Interface SHALL show the subtitle "How can I help you today?" below the title
5. WHEN messages are displayed, THE Chat_Interface SHALL format them clearly with visual distinction between user and agent messages

### Requirement 2: User Input Processing

**User Story:** As a user, I want to send messages to the insurance agent, so that I can get help with my insurance needs.

#### Acceptance Criteria

1. WHEN a user types a message and presses Enter or clicks send, THE Chat_Interface SHALL capture the input and add it to the conversation
2. WHEN a message is sent, THE Chat_Interface SHALL clear the input field for the next message
3. WHEN user input is received, THE Gemini_LLM SHALL process the message and generate an appropriate response
4. THE Chat_Interface SHALL prevent sending empty messages
5. WHEN a response is generated, THE Chat_Interface SHALL display it immediately in the conversation history

### Requirement 3: Sidebar Information Display

**User Story:** As a user, I want to see session information and controls, so that I can understand my conversation progress and manage the session.

#### Acceptance Criteria

1. THE Chat_Interface SHALL display session statistics including message count and user information collected
2. THE Chat_Interface SHALL show the current conversation state (greeting, support_flow, sales_flow, etc.)
3. THE Chat_Interface SHALL provide a "Clear Conversation" button in the sidebar
4. WHEN the Clear Conversation button is clicked, THE State_Manager SHALL reset all conversation data
5. THE sidebar SHALL update automatically as the conversation progresses

### Requirement 4: State Persistence

**User Story:** As a user, I want my conversation to persist during my session, so that I don't lose context when the interface refreshes.

#### Acceptance Criteria

1. THE State_Manager SHALL persist all conversation data across Streamlit reruns
2. THE State_Manager SHALL maintain conversation history without loss during interface updates
3. THE State_Manager SHALL preserve session statistics across reruns
4. THE State_Manager SHALL maintain current conversation state across reruns
5. WHEN the application restarts, THE State_Manager SHALL initialize with empty state unless explicitly preserved

### Requirement 5: AI Response Generation

**User Story:** As a user, I want to receive intelligent responses from the insurance agent, so that I can get meaningful help with insurance-related questions.

#### Acceptance Criteria

1. THE Gemini_LLM SHALL generate contextually appropriate responses to user messages
2. THE Gemini_LLM SHALL maintain conversation context across multiple message exchanges
3. THE Gemini_LLM SHALL support different conversation flows including greeting, support_flow, and sales_flow
4. WHEN processing user input, THE Gemini_LLM SHALL respond within a reasonable time frame
5. THE Gemini_LLM SHALL handle insurance-specific queries and provide relevant information

### Requirement 6: Conversation Flow Management

**User Story:** As a user, I want the agent to guide me through appropriate conversation flows, so that I can efficiently accomplish my insurance-related goals.

#### Acceptance Criteria

1. THE Sentinel SHALL initialize conversations with a greeting flow
2. THE Sentinel SHALL transition between conversation states based on user intent and context
3. THE Sentinel SHALL track the current conversation state and display it in the sidebar
4. WHEN a user indicates support needs, THE Sentinel SHALL enter support_flow state
5. WHEN a user indicates sales interest, THE Sentinel SHALL enter sales_flow state

### Requirement 7: Session Management

**User Story:** As a user, I want to manage my conversation session, so that I can start fresh when needed or continue existing conversations.

#### Acceptance Criteria

1. THE Sentinel SHALL assume single-user operation for Stage 1
2. THE Sentinel SHALL maintain session continuity until explicitly cleared
3. WHEN the Clear Conversation button is activated, THE Sentinel SHALL reset to initial greeting state
4. THE Sentinel SHALL track and display session metrics including message count
5. THE Sentinel SHALL collect and display user information gathered during the conversation

### Requirement 8: Error Handling and Reliability

**User Story:** As a user, I want the system to handle errors gracefully, so that I can continue my conversation even when issues occur.

#### Acceptance Criteria

1. WHEN the Gemini_LLM is unavailable, THE Sentinel SHALL display an appropriate error message
2. WHEN network issues occur, THE Sentinel SHALL maintain conversation state and retry operations
3. IF message processing fails, THE Sentinel SHALL inform the user and allow them to retry
4. THE Sentinel SHALL handle malformed user input gracefully without crashing
5. WHEN errors occur, THE Sentinel SHALL log appropriate information for debugging while maintaining user privacy