# Implementation Plan: Streamlit Insurance Agent Simplification

## Overview

This implementation plan transforms an over-engineered Python Streamlit insurance agent application (50+ files) into a clean, maintainable Stage 1 MVP (9-11 files). The approach focuses on systematic simplification while preserving all core functionality including conversation flow management, Gemini AI integration, and user information collection.

## Tasks

- [x] 1. Analyze current system structure
  - Document the current file structure and dependencies
  - Identify all files to be removed vs. simplified vs. preserved
  - Create basic simplified Streamlit app for testing after each major task
  - _Requirements: 2.1, 2.3_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 2. Set up simplified project structure
  - [x] 2.1 Create new simplified directory structure
    - Set up the target directory structure with core folders
    - Create placeholder files for all target modules
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Create simplified requirements.txt
    - Extract only essential dependencies: streamlit, google-generativeai, python-dotenv
    - Remove all development, testing, and documentation dependencies
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 2.3 Manually verify requirements
    - Check that config loads correctly
    - Verify API key is read from .env
    - Print config values to console
    - _Requirements: 5.5_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 3. Migrate core data models (quick)
  - [x] 3.1 Copy and preserve models.py
    - Copy existing UserInfo and ConversationState dataclasses
    - Ensure all data validation methods are preserved
    - _Requirements: 2.2, 6.5_
  
  - [x] 3.2 Manual verification of data models
    - Test UserInfo and ConversationState creation
    - Verify data validation methods work
    - _Requirements: 1.4, 8.4_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 4. Create simplified configuration system (quick)
  - [x] 4.1 Implement simplified config.py
    - Replace complex configuration with basic environment variable reading
    - Implement load_config(), get_api_key(), and validate_required_config()
    - Remove all validation complexity while preserving functionality
    - _Requirements: 4.1, 4.5_
  
  - [x] 4.2 Create .env.example template
    - Provide simple template with GEMINI_API_KEY and other required variables
    - Include clear comments for each configuration option
    - _Requirements: 4.4_
  
  - [x] 4.3 Manual verification of config system
    - Print and import the correct variables to verify functionality
    - Validate configuration loading works properly
    - Test with missing API key to verify error handling
    - _Requirements: 4.3, 8.5, 11.5_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 5. Simplify Gemini client integration (critical path)
  - [x] 5.1 Create simplified gemini_client.py
    - Preserve core API integration functionality
    - Implement generate_response(), format_response(), and handle_api_error()
    - Remove extensive error handling, keep essential API communication
    - Be mindful of Gemini API rate limits (per minute and per day)
    - _Requirements: 3.1, 8.3_
  
  - [x] 5.2 Manual verification of Gemini integration
    - Handle 429 resource exhausted and similar API errors
    - Test with dummy API key and verify error handling
    - Test with valid API key (if available) with simple prompt
    - Verify rate limit handling
    - _Requirements: 8.3, 11.1, 11.2, 11.3, 11.4_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 6. Migrate conversation flow manager (depends on Gemini)
  - [x] 6.1 Simplify conversation_flow_manager.py
    - Preserve core conversation logic: process_message(), extract_user_info(), determine_intent(), transition_state()
    - Remove complex state management, use direct integration with Streamlit session_state
    - Integrate with simplified Gemini client
    - _Requirements: 2.2, 8.2, 8.4_
  
  - [x] 6.2 Manual verification of conversation flow manager
    - Verify conversation state management works correctly
    - Test with various conversation scenarios
    - Test integration with Gemini client
    - _Requirements: 1.2, 1.3, 8.2_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 7. Consolidate prompts system (can be done in parallel)
  - [x] 7.1 Create unified prompts.py
    - Consolidate all prompts from multiple files into single dictionary structure
    - Implement SYSTEM_PROMPTS, INTENT_PATTERNS, and RESPONSE_TEMPLATES
    - Preserve all prompt content and functionality
    - _Requirements: 2.4, 7.5_
  
  - [x] 7.2 Manual verification of prompts system
    - Test that all prompts are accessible
    - Verify prompt formatting works correctly
    - _Requirements: 1.5_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 8. Create simplified main application (brings it all together)
  - [x] 8.1 Implement simplified app.py
    - Replace complex orchestration with straightforward Streamlit interface
    - Implement main(), handle_user_input(), display_conversation_history(), initialize_session_state()
    - Use Streamlit session_state directly instead of custom state management
    - _Requirements: 3.2, 7.2_
  
  - [x] 8.2 Implement inline error handling
    - Replace centralized error handling with simple try/catch blocks
    - Add user-friendly error messages for common failure scenarios
    - Implement basic logging using Python's logging module
    - _Requirements: 3.1, 3.3, 7.1, 7.3_
  
  - [x] 8.3 Implement basic input validation
    - Replace complex input_manager with simple validation in app.py
    - Add validate_input() function for basic input checking
    - _Requirements: 3.4, 7.4_
  
  - [ ] **PAUSE FOR COMMIT** - User commits progress to git

- [x] 9. Final cleanup and documentation
  - [x] 9.1 Remove over-engineered components
    - Delete unnecessary files and directories (keep notes.md)
    - Remove all test files (tests/ directory and test_*.py files)
    - Remove excessive documentation files (*_SUMMARY.md, INSTALLATION.md, USER_GUIDE.md, API_REFERENCE.md)
    - Remove validation and debugging scripts (validate_*.py, debug_*.py, integration_test.py)
    - Remove over-engineered modules (privacy_logger.py, state_manager.py, error_handler.py, input_manager.py)
    - Remove configuration scripts (setup_config.py, CONFIG_SETUP.md)
    - _Requirements: 2.3, 3.5_
  
  - [x] 9.2 Verify file count reduction
    - Count remaining files and ensure total is 9-11 files
    - Verify all target files are present and functional
    - _Requirements: 2.1, 6.1_
  
  - [x] 9.3 Write comprehensive README.md
    - Create single documentation file with 3-5 step setup instructions
    - Document all environment variables and configuration options
    - Provide clear examples of .env file setup
    - Include troubleshooting section for common issues
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 9.4 Final verification checklist
    - [ ] Start app: `streamlit run app.py`
    - [ ] Test: Send "Hello" → Should get greeting
    - [ ] Test: Say "I need help with my policy" → Should transition to support
    - [ ] Test: Say "I want to buy insurance" → Should transition to sales
    - [ ] Test: Provide name → Should be stored in session_state
    - [ ] Test: Conversation history persists across messages
    - [ ] Test: Invalid API key shows error message
    - [ ] Test: Count files (should be 9-11)
    - [ ] Test: Count lines of code (should be 500-800)
    - [ ] Verify all essential functionality is preserved
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1, 8.2, 8.4, 4.3, 8.5, 11.5, 6.1, 6.5, 8.3_
  
  - [ ] **FINAL PAUSE FOR COMMIT** - User commits final version to git

## Notes

- Each task includes a pause for git commits to track progress incrementally
- Basic simplified Streamlit app will be created early for testing after each major task
- Manual verification replaces property tests for practical validation
- Tool calls removed for this stage - will be tackled separately
- Tasks restructured for logical dependency flow: Analysis → Structure → Models → Config → Gemini (critical path) → Flow Manager → Prompts → App → Cleanup
- Final verification broken into detailed checklist for thorough testing
- Be mindful of Gemini API rate limits (per minute and per day) during testing
- The migration strategy preserves core business logic while removing unnecessary complexity
- User will be prompted after every task completion for git commits