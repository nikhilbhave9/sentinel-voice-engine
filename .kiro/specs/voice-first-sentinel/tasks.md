# Implementation Plan: Voice-First Sentinel Command Center

## Overview

This implementation plan transforms the Sentinel Insurance Agent from a hybrid text-and-voice system into a pure voice-first command center. The refactoring involves three main areas:

1. **Enhanced Tool Logic**: Update `lookup_policy` to return structured responses with escalation indicators
2. **Automatic Escalation Flow**: Modify conversation flow manager to detect and handle escalation automatically
3. **Command Center UI**: Complete redesign of the Streamlit interface with real-time metrics, live transcription, and dark theme

The implementation maintains the existing voice pipeline (Faster-Whisper STT, Piper TTS, Gemini 2.5 Flash Lite) while adding performance monitoring and improving the voice-only user experience.

## Tasks

- [x] 1. Create latency tracking infrastructure
  - Create new file `src/core/metrics.py` with `LatencyMetrics` dataclass and `track_latency` context manager
  - Implement methods for tracking STT, LLM, and TTS latency
  - Add `to_dict()` method for easy serialization to session state
  - _Requirements: 4.2, 4.3, 4.4, 8.1, 8.2, 8.3, 8.4_

- [ ] 2. Enhance tool response structure
  - [x] 2.1 Update lookup_policy tool with escalation detection
    - Modify `src/core/tools.py` to return structured dictionary responses instead of strings
    - Add `operation` parameter to `lookup_policy` function (default: "lookup")
    - Implement escalation detection for unsupported operations (change_address, claim_status, update_beneficiary)
    - Return structured response with fields: status, action, escalation_required, data, message
    - Maintain backward compatibility with existing policy lookup functionality
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 2.2 Write unit tests for lookup_policy escalation logic
    - Test successful policy lookup returns escalation_required=false
    - Test unsupported operations return status="not_supported" and action="escalate"
    - Test policy not found returns appropriate error response
    - Test all unsupported operation keywords trigger escalation
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3. Implement automatic escalation flow
  - [x] 3.1 Add escalation detection to conversation flow manager
    - Create `detect_escalation_from_tool_result()` function in `src/core/conversation_flow_manager.py`
    - Handle both dictionary and string tool responses for backward compatibility
    - Check for escalation_required field, status="not_supported", and action="escalate"
    - _Requirements: 2.1, 10.2, 10.3, 10.4_

  - [x] 3.2 Update process_message to handle automatic escalation
    - Modify `process_message()` in `src/core/conversation_flow_manager.py` to check tool results for escalation
    - When escalation detected, append message: "I'll need a specialist for that. Let me get someone from the department on the line."
    - Automatically invoke `triage_and_escalate` tool with collected user info (name, issue description, phone)
    - Handle missing information by collecting it before triggering escalation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 3.3 Write unit tests for escalation flow
    - Test escalation detection from tool results
    - Test automatic escalation message generation
    - Test triage_and_escalate is called with correct parameters
    - Test missing information collection before escalation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Integrate latency tracking into voice pipeline
  - [x] 4.1 Add latency tracking to STT processing
    - Update `transcribe_audio()` in `src/voice/streamlit_voice_handler.py` to track STT latency
    - Use `track_latency` context manager to measure transcription time
    - Return latency measurement along with transcription result
    - _Requirements: 8.1, 4.2_

  - [x] 4.2 Add latency tracking to LLM processing
    - Update `generate_response()` in `src/integration/gemini_client.py` to track LLM latency
    - Measure time from request to response completion
    - Return latency and token count in response metadata
    - _Requirements: 8.2, 4.3_

  - [x] 4.3 Add latency tracking to TTS processing
    - Update `synthesize_speech()` in `src/voice/streamlit_voice_handler.py` to track TTS latency
    - Use `track_latency` context manager to measure synthesis time
    - Return latency measurement along with audio path
    - _Requirements: 8.3, 4.4_

- [x] 5. Checkpoint - Verify backend enhancements
  - Ensure all tests pass for tool logic and escalation flow
  - Verify latency tracking is working correctly
  - Ask the user if questions arise

- [ ] 6. Implement command center UI theme
  - [x] 6.1 Create dark theme CSS styling
    - Add `apply_command_center_theme()` function in `app.py`
    - Implement dark background (#0e1117) with high-contrast text
    - Style metric cards with dark theme (#1e2130 background, #2e3440 borders)
    - Style transcription container with monospace font and dark theme
    - Add color-coded status indicators (green for active, yellow for processing, red for error)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.2 Update page configuration
    - Modify `st.set_page_config()` to use wide layout and collapsed sidebar
    - Update page title to "Sentinel Command Center"
    - Apply command center theme on app initialization
    - _Requirements: 6.1, 6.4_

- [ ] 7. Build stats dashboard component
  - [x] 7.1 Create stats dashboard rendering function
    - Implement `render_stats_dashboard()` function in `app.py`
    - Use Streamlit columns (5 columns) for metrics display
    - Display STT latency, LLM latency, TTS latency, token count, and model name
    - Pull metrics from session state `current_metrics`
    - Format latency values with "ms" suffix
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 7.2 Initialize metrics in session state
    - Add `current_metrics` to session state initialization
    - Initialize with default values (all zeros, model="N/A")
    - Update metrics after each voice interaction
    - _Requirements: 4.7, 8.4_

- [ ] 8. Build live transcription component
  - [x] 8.1 Create live transcription rendering function
    - Implement `render_live_transcription()` function in `app.py`
    - Use `st.empty()` for real-time updates
    - Build HTML display with user speech and agent responses
    - Apply visual formatting to distinguish user (cyan) vs agent (green) messages
    - Display messages in chronological order with role labels ([USER], [SENTINEL])
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 8.2 Update message storage format
    - Ensure messages in session state include role and content
    - Maintain source field for tracking voice vs text origin
    - Update live transcription display in real-time as messages are added
    - _Requirements: 5.3, 5.4, 5.5_

- [ ] 9. Implement voice-only interface
  - [x] 9.1 Remove text chat functionality
    - Remove text chat tab from `app.py`
    - Remove `render_text_chat_interface()` function
    - Remove text input components (st.chat_input)
    - Keep only voice interaction components
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 9.2 Restructure main interface layout
    - Remove tab structure from `main()` function
    - Create single-page layout with stats dashboard at top
    - Place live transcription in middle section
    - Place audio recorder at bottom
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 9.3 Update voice input section
    - Implement `render_voice_input()` function
    - Keep existing audio_recorder_streamlit component
    - Maintain model loading button and initialization flow
    - Update styling to match command center theme
    - _Requirements: 3.2, 3.5_

- [ ] 10. Implement automatic welcome message
  - [x] 10.1 Create welcome message generation function
    - Implement `play_welcome_message()` function in `app.py`
    - Generate welcome message: "Hello! I'm Sentinel. How can I help you today?"
    - Synthesize welcome audio using TTS after models load
    - Store welcome audio in session state for autoplay
    - Add welcome message to conversation history
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 10.2 Trigger welcome message on model initialization
    - Call `play_welcome_message()` after successful model loading
    - Display welcome text in live transcription immediately
    - Autoplay welcome audio without user interaction
    - Handle errors gracefully if welcome message generation fails
    - _Requirements: 11.1, 11.2, 11.4_

- [ ] 11. Update voice processing workflow
  - [x] 11.1 Integrate latency tracking into voice workflow
    - Update `render_voice_call_interface()` to collect latency from STT, LLM, and TTS
    - Store latency metrics in session state after each interaction
    - Update stats dashboard with new metrics
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 11.2 Update UI after voice processing
    - Update live transcription with user speech and agent response
    - Update stats dashboard with latest metrics
    - Maintain audio autoplay functionality
    - Trigger st.rerun() to refresh UI components
    - _Requirements: 4.7, 5.3, 5.4_

- [ ] 12. Clean up legacy code
  - [x] 12.1 Remove TTS patch file
    - Delete `src/voice/tts_patch.py` file (XTTS-specific, not needed for Piper)
    - Remove import statement for tts_patch from `src/voice/streamlit_voice_handler.py`
    - Verify no other components depend on the TTS patch
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 12.2 Remove XTTS dependencies
    - Check `requirements.txt` for XTTS-related packages
    - Remove any XTTS configuration or dependencies if present
    - Verify application runs correctly without XTTS components
    - _Requirements: 12.4_

- [ ] 13. Maintain voice performance optimization
  - [x] 13.1 Verify max_output_tokens configuration
    - Confirm max_output_tokens is set to 400 in Gemini client configuration
    - Ensure responses are optimized for voice delivery
    - Verify sentence limiting in `_limit_sentences()` is working correctly
    - _Requirements: 7.1, 7.2, 7.3, 7.6_

  - [x] 13.2 Verify voice model configuration
    - Confirm Piper TTS is using en_US-lessac-medium voice
    - Confirm Faster-Whisper is using tiny model for STT
    - Verify VAD parameters are optimized for voice input
    - _Requirements: 7.4, 7.5_

- [ ] 14. Update conversation state preservation
  - [x] 14.1 Verify ConversationStateData structure
    - Confirm existing ConversationStateData structure is maintained
    - Verify user information is preserved across voice interactions
    - Ensure conversation history is maintained for context
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 14.2 Test escalation with conversation state
    - Verify collected user information is passed to triage_and_escalate
    - Test conversation state persists throughout voice session
    - Ensure state transitions work correctly with escalation flow
    - _Requirements: 9.4, 9.5_

- [ ] 15. Final integration and testing
  - [x] 15.1 Integration testing for complete voice workflow
    - Test end-to-end voice interaction: recording → STT → LLM → TTS → playback
    - Verify stats dashboard updates correctly with each interaction
    - Verify live transcription displays messages in real-time
    - Test automatic welcome message on initialization
    - _Requirements: 4.7, 5.3, 5.4, 11.1, 11.4_

  - [x] 15.2 Test escalation scenarios
    - Test unsupported operation detection (address change, claim status, beneficiary update)
    - Verify automatic escalation message is delivered
    - Verify triage_and_escalate is called with correct parameters
    - Test escalation with missing user information
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 15.3 Performance testing
    - Measure latency for each processing stage (STT, LLM, TTS)
    - Verify latency tracking does not impact system performance
    - Test with various audio input lengths
    - Verify max_output_tokens prevents mid-sentence cutoffs
    - _Requirements: 7.1, 8.5, 8.6_

- [x] 16. Final checkpoint - Ensure all tests pass
  - Verify all functionality works end-to-end
  - Confirm UI matches command center aesthetic
  - Ensure voice-only interaction is smooth and responsive
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- The implementation maintains existing voice processing pipeline while adding new features
- Focus on voice-first experience with real-time performance monitoring
- Dark theme and command center aesthetic enhance the professional feel
