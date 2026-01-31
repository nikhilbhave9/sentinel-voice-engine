# Requirements Document

## Introduction

This specification defines the requirements for simplifying an over-engineered Python Streamlit insurance agent application into a Stage 1 MVP. The current system has ~50+ files with extensive testing, documentation, and validation infrastructure that needs to be reduced to ~10-15 essential files while maintaining all core functionality.

## Glossary

- **System**: The simplified Streamlit insurance agent application
- **Core_Functionality**: Essential features that must be preserved (conversation flow, AI integration, user info collection)
- **Over_Engineered_Components**: Complex modules that will be removed or simplified (privacy_logger, state_manager, error_handler, etc.)
- **Gemini_Client**: The AI integration component for processing user conversations
- **Conversation_State**: The current state of user interaction (greeting, support_flow, sales_flow)
- **User_Info**: Collected user data (name, policy_number, contact_info, inquiry_type)
- **Session_State**: Streamlit's built-in state management system

## Requirements

### Requirement 1: Core Functionality Preservation

**User Story:** As a user, I want the simplified application to maintain all essential features, so that I can continue using the insurance agent without any loss of functionality.

#### Acceptance Criteria

1. WHEN a user inputs text, THE System SHALL process it through Gemini AI and return a response
2. WHEN a user engages in conversation, THE System SHALL maintain conversation history in session state
3. WHEN the conversation progresses, THE System SHALL manage conversation states (greeting, support_flow, sales_flow)
4. WHEN user information is needed, THE System SHALL collect name, policy_number, contact_info, and inquiry_type
5. WHEN different conversation states are active, THE System SHALL use appropriate system prompts

### Requirement 2: File Structure Simplification

**User Story:** As a developer, I want a dramatically simplified file structure, so that the codebase is maintainable and easy to understand.

#### Acceptance Criteria

1. THE System SHALL reduce total files from 50+ to 10-15 essential files
2. THE System SHALL maintain only core modules: models.py, config.py, conversation_flow_manager.py, prompts.py, tools.py, gemini_client.py, and app.py
3. THE System SHALL eliminate all test files, excessive documentation, and validation scripts
4. THE System SHALL consolidate all prompts into a single prompts.py file
5. THE System SHALL create a single comprehensive README.md with setup instructions

### Requirement 3: Over-Engineered Component Removal

**User Story:** As a developer, I want to remove unnecessary complexity, so that the codebase is simpler and easier to maintain.

#### Acceptance Criteria

1. THE System SHALL remove privacy_logger.py and replace with basic Python logging
2. THE System SHALL remove state_manager.py and use Streamlit's session_state directly
3. THE System SHALL remove error_handler.py and implement simple try/catch blocks in app.py
4. THE System SHALL remove input_manager.py and implement basic validation in app.py
5. THE System SHALL remove all validation scripts, debugging scripts, and integration test files

### Requirement 4: Configuration Simplification

**User Story:** As a developer, I want simplified configuration management, so that setup is straightforward and maintainable.

#### Acceptance Criteria

1. THE System SHALL simplify config.py to basic environment variable reading
2. THE System SHALL remove setup_config.py and CONFIG_SETUP.md
3. THE System SHALL maintain API key configuration via .env file
4. THE System SHALL provide a simple .env.example template
5. THE System SHALL reduce configuration complexity while preserving functionality

### Requirement 5: Dependencies and Requirements Optimization

**User Story:** As a developer, I want minimal dependencies, so that the application is lightweight and has fewer potential conflicts.

#### Acceptance Criteria

1. THE System SHALL maintain only essential dependencies in requirements.txt
2. THE System SHALL remove development, testing, and documentation dependencies
3. THE System SHALL preserve core dependencies: streamlit, google-generativeai, python-dotenv
4. THE System SHALL ensure all remaining dependencies are necessary for core functionality
5. THE System SHALL validate that the simplified requirements.txt works for fresh installations

### Requirement 6: Code Volume Reduction

**User Story:** As a developer, I want significantly reduced code volume, so that the system is easier to understand and maintain.

#### Acceptance Criteria

1. THE System SHALL reduce total lines of code from 2000+ to 500-800 lines
2. THE System SHALL maintain code readability while removing unnecessary complexity
3. THE System SHALL consolidate related functionality into fewer files
4. THE System SHALL remove redundant code and over-abstracted patterns
5. THE System SHALL preserve all essential business logic during simplification

### Requirement 7: Migration and Integration Strategy

**User Story:** As a developer, I want a clear migration path, so that I can systematically transform the over-engineered system.

#### Acceptance Criteria

1. WHEN migrating privacy_logger functionality, THE System SHALL replace with standard Python logging
2. WHEN migrating state_manager functionality, THE System SHALL use Streamlit session_state directly
3. WHEN migrating error_handler functionality, THE System SHALL implement inline error handling
4. WHEN migrating input_manager functionality, THE System SHALL implement basic validation in app.py
5. WHEN consolidating prompts, THE System SHALL preserve all prompt content and functionality

### Requirement 8: Quality Assurance and Validation

**User Story:** As a developer, I want to ensure the simplified system works correctly, so that no functionality is lost during simplification.

#### Acceptance Criteria

1. THE System SHALL maintain identical user experience (same input/output behavior)
2. THE System SHALL preserve all conversation flow logic including intent detection and state transitions
3. THE System SHALL maintain working Gemini AI integration with proper error handling
4. THE System SHALL ensure user info collection functions identically to the original
5. THE System SHALL validate that API key configuration works through .env files

### Requirement 9: Documentation and Setup

**User Story:** As a new developer, I want clear setup instructions, so that I can quickly get the simplified application running.

#### Acceptance Criteria

1. THE System SHALL provide a single comprehensive README.md file
2. THE System SHALL include 3-5 step setup instructions in the README
3. THE System SHALL document all environment variables and configuration options
4. THE System SHALL provide clear examples of .env file setup
5. THE System SHALL remove all other documentation files (installation guides, API references, etc.)

### Requirement 10: Function/Tool Call Support

**User Story:** As a user, I want the agent to be able to perform specific insurance-related actions, so that I can get policy information, check claim status, and schedule appointments.

#### Acceptance Criteria

1. THE System SHALL provide a tools.py module with available function definitions
2. THE System SHALL support policy lookup functionality that returns dummy data during development
3. THE System SHALL support claim status checking that returns dummy data during development
4. THE System SHALL support appointment scheduling that returns dummy data during development
5. THE System SHALL provide a function dispatcher to execute requested functions

### Requirement 11: Gemini Integration Preservation

**User Story:** As a user, I want the AI functionality to work identically, so that my conversations with the insurance agent are unaffected.

#### Acceptance Criteria

1. THE Gemini_Client SHALL maintain all essential API integration functionality
2. THE Gemini_Client SHALL preserve conversation context and history handling
3. THE Gemini_Client SHALL maintain proper error handling for API failures
4. THE Gemini_Client SHALL preserve response processing and formatting
5. THE Gemini_Client SHALL work with the same API key configuration as the original system