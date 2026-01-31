# Design Document: Streamlit Insurance Agent Simplification

## Overview

This design outlines the transformation of an over-engineered Python Streamlit insurance agent application into a clean, maintainable Stage 1 MVP. The current system with 50+ files will be reduced to 8-10 essential files while preserving all core functionality including conversation flow management, Gemini AI integration, and user information collection.

The simplification strategy focuses on removing abstraction layers, consolidating related functionality, and replacing complex patterns with straightforward implementations. The result will be a system that is easier to understand, maintain, and extend while providing identical user experience.

## Architecture

### Current Architecture Problems
The existing system suffers from over-engineering patterns:
- Excessive abstraction layers (privacy_logger, state_manager, error_handler)
- Complex configuration management with validation scripts
- Extensive testing infrastructure for an MVP
- Multiple documentation files creating maintenance overhead
- Scattered prompt management across multiple files

### Simplified Architecture
The new architecture follows a flat, straightforward structure:

```
Streamlit App (app.py)
    ↓
Conversation Flow Manager
    ↓
Gemini Client ← → Configuration
    ↓
User Models & Prompts
```

**Key Architectural Decisions:**
1. **Direct Integration**: Remove abstraction layers between components
2. **Streamlit-Native State**: Use session_state instead of custom state management
3. **Inline Error Handling**: Replace centralized error handling with contextual try/catch
4. **Single Prompt File**: Consolidate all prompts for easier management
5. **Minimal Configuration**: Simple environment variable reading

## Components and Interfaces

### Core Components

#### 1. Main Application (app.py)
**Purpose**: Streamlit interface and application orchestration
**Responsibilities**:
- User interface rendering
- Input/output handling
- Session state management
- Basic error handling and logging
- Integration with conversation flow manager

**Key Functions**:
- `main()`: Application entry point
- `handle_user_input(user_input: str)`: Process user messages
- `display_conversation_history()`: Render chat history
- `initialize_session_state()`: Set up initial state

#### 2. Conversation Flow Manager (src/core/conversation_flow_manager.py)
**Purpose**: Core conversation logic and state management
**Responsibilities**:
- Intent detection and conversation state transitions
- User information extraction and validation
- Conversation flow orchestration
- Integration with Gemini client

**Preserved Functions**:
- `process_message(message: str, state: ConversationState)`: Main processing logic
- `extract_user_info(message: str)`: Information extraction
- `determine_intent(message: str)`: Intent classification
- `transition_state(current_state: str, intent: str)`: State management

#### 3. Gemini Client (src/integration/gemini_client.py)
**Purpose**: Simplified AI integration
**Responsibilities**:
- API communication with Google Gemini
- Response processing and formatting
- Basic error handling for API failures
- Conversation context management

**Simplified Interface**:
- `generate_response(prompt: str, context: str)`: Main API call
- `format_response(raw_response: str)`: Response processing
- `handle_api_error(error: Exception)`: Basic error handling

#### 4. Data Models (src/core/models.py)
**Purpose**: Core data structures (preserved as-is)
**Components**:
- `UserInfo`: User data collection
- `ConversationState`: State management
- Data validation methods

#### 5. Configuration (src/core/config.py)
**Purpose**: Simplified environment configuration
**Responsibilities**:
- Environment variable reading
- API key management
- Basic validation

**Simplified Interface**:
- `load_config()`: Load environment variables
- `get_api_key()`: Retrieve Gemini API key
- `validate_required_config()`: Basic validation

#### 6. Prompts (src/core/prompts.py)
**Purpose**: Consolidated prompt management
**Responsibilities**:
- System prompts for different conversation states
- Intent detection patterns
- Response templates

**Structure**:
- `SYSTEM_PROMPTS`: Dictionary of state-specific prompts
- `INTENT_PATTERNS`: Regex patterns for intent detection
- `RESPONSE_TEMPLATES`: Standard response formats

#### 7. Tools and Functions (src/core/tools.py)
**Purpose**: Function/tool call handling for agent interactions
**Responsibilities**:
- Define available functions that the agent can call
- Handle function execution and return appropriate responses
- Provide dummy data during development/testing phases
- Support insurance-specific operations (policy lookup, claim status, etc.)

**Structure**:
- `AVAILABLE_FUNCTIONS`: Dictionary of callable functions
- `execute_function(function_name: str, parameters: dict)`: Function dispatcher
- `get_policy_info(policy_number: str)`: Policy lookup (returns dummy data)
- `check_claim_status(claim_id: str)`: Claim status check (returns dummy data)
- `schedule_appointment(date: str, time: str)`: Appointment scheduling (returns dummy data)

## Data Models

### Preserved Models
The existing data models in `src/core/models.py` will be preserved as they represent the core domain logic:

```python
@dataclass
class UserInfo:
    name: Optional[str] = None
    policy_number: Optional[str] = None
    contact_info: Optional[str] = None
    inquiry_type: Optional[str] = None

@dataclass
class ConversationState:
    current_state: str = "greeting"
    user_info: UserInfo = field(default_factory=UserInfo)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
```

### Session State Structure
Streamlit session state will directly store:
- `conversation_state`: ConversationState instance
- `messages`: List of conversation messages
- `initialized`: Boolean flag for initialization

## Migration Strategy

### Component Migration Plan

#### 1. Privacy Logger → Python Logging
**Current**: Complex privacy-aware logging system
**Target**: Standard Python logging with basic configuration
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

#### 2. State Manager → Streamlit Session State
**Current**: Custom state management with persistence
**Target**: Direct use of `st.session_state`
```python
# Replace state_manager.get_state()
if 'conversation_state' not in st.session_state:
    st.session_state.conversation_state = ConversationState()
```

#### 3. Error Handler → Inline Error Handling
**Current**: Centralized error handling with complex recovery
**Target**: Simple try/catch blocks with user-friendly messages
```python
try:
    response = gemini_client.generate_response(prompt)
except Exception as e:
    st.error("Sorry, I'm having trouble processing your request. Please try again.")
    logger.error(f"Gemini API error: {e}")
```

#### 4. Input Manager → Basic Validation
**Current**: Complex input validation and sanitization
**Target**: Simple validation in app.py
```python
def validate_input(user_input: str) -> bool:
    return bool(user_input and user_input.strip())
```

#### 5. Prompts Consolidation
**Current**: Multiple prompt files and complex loading
**Target**: Single prompts.py file with dictionary structure
```python
SYSTEM_PROMPTS = {
    "greeting": "You are a helpful insurance agent...",
    "support_flow": "You are assisting with a support inquiry...",
    "sales_flow": "You are helping with insurance sales..."
}
```

### File Elimination Strategy

#### Files to Remove Completely:
1. **All test files**: `tests/` directory and `test_*.py` files
2. **Documentation files**: `*_SUMMARY.md`, `INSTALLATION.md`, `USER_GUIDE.md`, `API_REFERENCE.md`
3. **Validation scripts**: `validate_*.py`, `debug_*.py`, `integration_test.py`
4. **Configuration scripts**: `setup_config.py`, `CONFIG_SETUP.md`
5. **Over-engineered modules**: `privacy_logger.py`, `state_manager.py`, `error_handler.py`, `input_manager.py`

#### Files to Simplify:
1. **config.py**: Remove validation complexity, keep essential environment reading
2. **gemini_client.py**: Remove extensive error handling, keep core API integration
3. **app.py**: Simplify orchestration, remove complex state management
4. **requirements.txt**: Keep only essential dependencies

## Error Handling

### Simplified Error Handling Strategy
Replace the complex centralized error handling system with straightforward, contextual error management:

#### 1. API Errors
```python
try:
    response = gemini_client.generate_response(prompt)
except requests.exceptions.RequestException:
    st.error("Network error. Please check your connection and try again.")
except Exception as e:
    st.error("Sorry, I'm having trouble right now. Please try again in a moment.")
    logger.error(f"Unexpected error: {e}")
```

#### 2. Configuration Errors
```python
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
except ValueError as e:
    st.error("Configuration error. Please check your .env file.")
    st.stop()
```

#### 3. User Input Validation
```python
if not user_input or not user_input.strip():
    st.warning("Please enter a message.")
    return
```

## Testing Strategy

### Simplified Testing Approach
The MVP will rely on manual testing and basic validation rather than extensive automated testing:

#### 1. Manual Testing Checklist
- Conversation flow functionality
- User information collection
- Gemini API integration
- Session state persistence
- Error handling scenarios

#### 2. Basic Validation
- Configuration loading validation
- API key presence check
- Essential dependency verification

#### 3. Integration Verification
- End-to-end conversation flow
- State transitions
- AI response generation

### Rationale for Minimal Testing
For a Stage 1 MVP focused on simplification:
- Manual testing provides sufficient coverage for core functionality
- Automated testing infrastructure adds complexity counter to simplification goals
- Focus on working software over comprehensive test coverage
- Future iterations can add testing as needed

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis and property reflection, the following properties ensure the simplified system maintains all essential functionality:

### Property 1: Core Functionality Preservation
*For any* valid user input text, the simplified system should process it through Gemini AI and return a response while maintaining identical input/output behavior to the original system
**Validates: Requirements 1.1, 8.1**

### Property 2: Conversation State Management
*For any* sequence of user messages, the system should correctly manage conversation states (greeting, support_flow, sales_flow) and maintain conversation history in session state
**Validates: Requirements 1.2, 1.3, 8.2**

### Property 3: User Information Collection
*For any* message containing user information, the system should extract name, policy_number, contact_info, and inquiry_type with the same accuracy as the original system
**Validates: Requirements 1.4, 8.4**

### Property 4: Prompt System Consistency
*For any* conversation state, the system should use the appropriate system prompt from the consolidated prompts.py file
**Validates: Requirements 1.5**

### Property 5: Gemini Integration Reliability
*For any* valid API configuration, the Gemini client should maintain all essential functionality including conversation context handling, response processing, and error handling for API failures
**Validates: Requirements 8.3, 10.1, 10.2, 10.3, 10.4**

### Property 6: Function/Tool Call Handling
*For any* valid function call request (policy lookup, claim status, appointment scheduling), the system should execute the appropriate function and return dummy data in the expected format
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 7: Configuration Compatibility
*For any* valid .env file configuration, the system should successfully load API keys and configuration settings using the same format as the original system
**Validates: Requirements 4.3, 8.5, 11.5**