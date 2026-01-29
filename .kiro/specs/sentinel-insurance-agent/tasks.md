# Implementation Plan: Sentinel Insurance Agent Stage 1

## Overview

This implementation plan breaks down the Sentinel insurance agent into discrete coding tasks that build incrementally toward a functional text-based conversational interface. Each task focuses on implementing specific components while ensuring integration with previous work. The plan emphasizes early validation through testing and checkpoints to catch issues quickly.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure for the Streamlit application
  - Set up requirements.txt with Streamlit, google-genai, and testing dependencies
  - Create main application entry point (app.py)
  - Initialize basic Streamlit configuration
  - _Requirements: 7.1_

- [x] 2. Implement core data models and state management
  - [x] 2.1 Create data models for Message, SessionStats, and UserInfo
    - Implement dataclasses for all core data structures
    - Add validation methods for data integrity
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 2.2 Write property test for state persistence
    - **Property 4: State Persistence Across Reruns**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [x] 2.3 Implement State Manager class
    - Create StateManager with initialize_state, add_message, update_conversation_state methods
    - Implement session statistics tracking and user info collection
    - Use Streamlit session state for persistence
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 7.4, 7.5_

  - [ ]* 2.4 Write property test for session statistics accuracy
    - **Property 6: Session Statistics Accuracy**
    - **Validates: Requirements 3.1, 3.2, 7.4, 7.5**

- [ ] 3. Implement Gemini API integration
  - [x] 3.1 Create Gemini API client class
    - Implement GeminiClient with initialize_client and generate_response methods
    - Add error handling for API failures and timeouts
    - Configure model parameters (gemini-1.5-flash, temperature=0.7)
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 8.1_

  - [ ]* 3.2 Write property test for AI response generation
    - **Property 8: AI Response Generation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

  - [ ]* 3.3 Write property test for error handling
    - **Property 10: Error Handling Gracefully**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [ ] 4. Implement conversation flow management
  - [ ] 4.1 Create ConversationFlowManager class
    - Implement state transition logic for greeting, support_flow, sales_flow
    - Add intent detection for routing user inputs to appropriate flows
    - Create system prompts for different conversation states
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ]* 4.2 Write property test for conversation state transitions
    - **Property 5: Conversation State Transitions**
    - **Validates: Requirements 6.2, 6.4, 6.5**

  - [ ] 4.3 Implement input validation and processing
    - Create InputManager with validate_input, sanitize_input methods
    - Add empty input rejection and malformed input handling
    - _Requirements: 2.4, 8.4_

  - [ ]* 4.4 Write property test for empty input rejection
    - **Property 3: Empty Input Rejection**
    - **Validates: Requirements 2.4**

- [ ] 5. Checkpoint - Core logic validation
  - Ensure all core classes instantiate correctly
  - Verify state management and API integration work independently
  - Ask the user if questions arise

- [ ] 6. Implement chat interface components
  - [ ] 6.1 Create ChatInterface class
    - Implement render_chat_history with proper message formatting
    - Add render_chat_input for user message entry
    - Ensure user messages display on right, agent messages on left
    - _Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 2.5_

  - [ ]* 6.2 Write property test for message display consistency
    - **Property 1: Message Display Consistency**
    - **Validates: Requirements 1.1, 1.5**

  - [ ]* 6.3 Write property test for input processing completeness
    - **Property 2: Input Processing Completeness**
    - **Validates: Requirements 2.1, 2.2, 2.5**

  - [ ] 6.4 Add title and subtitle display
    - Display "🛡️ Sentinel Insurance Agent" title prominently
    - Show "How can I help you today?" subtitle
    - _Requirements: 1.3, 1.4_

  - [ ]* 6.5 Write unit tests for UI element presence
    - Test title, subtitle, and input box presence
    - _Requirements: 1.2, 1.3, 1.4_

- [ ] 7. Implement sidebar components
  - [ ] 7.1 Create SidebarComponent class
    - Implement render_session_stats to display message count and user info
    - Add render_conversation_state to show current flow state
    - Create render_clear_button for conversation reset
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 7.2 Write property test for sidebar state synchronization
    - **Property 9: Sidebar State Synchronization**
    - **Validates: Requirements 3.5, 6.3**

  - [ ]* 7.3 Write property test for conversation reset completeness
    - **Property 7: Conversation Reset Completeness**
    - **Validates: Requirements 3.4, 7.3**

- [ ] 8. Integrate all components in main application
  - [ ] 8.1 Create main Streamlit app structure
    - Wire together ChatInterface, SidebarComponent, and StateManager
    - Implement main conversation loop with user input processing
    - Add error handling and recovery mechanisms
    - _Requirements: 2.3, 5.4, 8.2, 8.3_

  - [ ] 8.2 Implement session continuity and initialization
    - Ensure proper app initialization with greeting state
    - Maintain session continuity across interactions
    - _Requirements: 6.1, 7.2_

  - [ ]* 8.3 Write property test for session continuity
    - **Property 11: Session Continuity**
    - **Validates: Requirements 7.2**

- [ ] 9. Add comprehensive error handling and logging
  - [ ] 9.1 Implement error handling across all components
    - Add try-catch blocks for API calls, state operations, and UI rendering
    - Create user-friendly error messages for different failure types
    - Implement retry mechanisms for transient failures
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 9.2 Add privacy-preserving logging
    - Implement logging that captures errors without exposing user data
    - Add debug information for troubleshooting
    - _Requirements: 8.5_

  - [ ]* 9.3 Write property test for privacy-preserving error logging
    - **Property 12: Privacy-Preserving Error Logging**
    - **Validates: Requirements 8.5**

- [ ] 10. Final integration and testing
  - [ ]* 10.1 Write integration tests for end-to-end conversation flows
    - Test complete conversation scenarios from greeting to support/sales flows
    - Verify all components work together correctly
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ] 10.2 Add environment configuration and API key setup
    - Create configuration for Gemini API key management
    - Add environment variable handling and validation
    - _Requirements: 5.1_

  - [ ] 10.3 Create application documentation and setup instructions
    - Add README with installation and usage instructions
    - Document environment setup and API key configuration
    - _Requirements: 7.1_

- [ ] 11. Final checkpoint - Complete system validation
  - Run all tests to ensure system works end-to-end
  - Verify all requirements are met through manual testing
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests focus on specific examples and integration points
- Checkpoints ensure incremental validation and early error detection
- All components should integrate cleanly without orphaned code