# Requirements Document

## Introduction

This document specifies the requirements for refactoring the Sentinel Insurance Agent from a text-and-voice hybrid system into a pure voice-first command center experience. The transformation focuses on enhancing tool logic for escalation handling, updating conversation flow to support automatic escalation, and redesigning the UI to provide a mission-critical command center aesthetic with real-time performance monitoring.

## Glossary

- **Sentinel**: The AI-powered insurance agent system
- **Voice_Handler**: Component responsible for speech-to-text (STT) and text-to-speech (TTS) processing
- **Tool**: A function that the LLM can call to perform specific actions (e.g., lookup_policy, triage_and_escalate)
- **Escalation**: The process of transferring a user request to a human specialist when the system cannot handle it
- **Command_Center_UI**: The redesigned voice-first user interface with real-time monitoring capabilities
- **Live_Transcription**: Real-time display of ongoing conversation showing both user speech and agent responses
- **Latency_Metrics**: Performance measurements for STT, LLM, and TTS processing times
- **Unsupported_Operation**: A user request that requires capabilities beyond the system's current scope

## Requirements

### Requirement 1: Tool Logic Enhancement for Escalation Detection

**User Story:** As a system architect, I want the lookup_policy tool to indicate when escalation is needed, so that the agent can automatically route unsupported requests to human specialists.

#### Acceptance Criteria

1. WHEN the lookup_policy function is called with a valid policy number, THE Sentinel SHALL return policy details with an escalation_required field set to false
2. WHEN a user requests an unsupported operation (address change, claim status, beneficiary update), THE lookup_policy function SHALL return a response with status "not_supported" and action "escalate"
3. WHEN the lookup_policy function returns an escalation indicator, THE response SHALL include the escalation_required boolean field
4. THE lookup_policy function SHALL maintain backward compatibility with existing policy lookup functionality
5. WHEN an unsupported operation is detected, THE tool response SHALL provide structured data that the conversation flow can parse

### Requirement 2: Automatic Escalation Flow

**User Story:** As a customer service manager, I want the agent to automatically detect when escalation is needed and trigger the handoff process, so that customers receive appropriate specialist support without manual intervention.

#### Acceptance Criteria

1. WHEN a tool returns a result indicating escalation is required, THE Sentinel SHALL detect this condition in the conversation flow
2. WHEN escalation is detected, THE Sentinel SHALL respond with the message "I'll need a specialist for that. Let me get someone from the department on the line."
3. WHEN the escalation message is delivered, THE Sentinel SHALL automatically invoke the triage_and_escalate tool
4. THE Sentinel SHALL extract the user's name, issue description, and phone number before calling triage_and_escalate
5. WHEN required information is missing for escalation, THE Sentinel SHALL collect it before triggering the escalation tool

### Requirement 3: Voice-Only Interface Transformation

**User Story:** As a product manager, I want to remove all text chat functionality, so that the system provides a focused voice-first experience.

#### Acceptance Criteria

1. THE Command_Center_UI SHALL remove the text chat tab and interface components
2. THE Command_Center_UI SHALL provide only voice input through the audio recorder
3. THE Command_Center_UI SHALL display conversation history in a voice-optimized format
4. WHEN the application starts, THE Command_Center_UI SHALL present only voice interaction options
5. THE Command_Center_UI SHALL maintain the existing audio_recorder_streamlit component for voice input

### Requirement 4: Command Center Dashboard Design

**User Story:** As a system operator, I want to see real-time performance metrics and conversation status, so that I can monitor system health and user experience quality.

#### Acceptance Criteria

1. THE Command_Center_UI SHALL display a stats dashboard at the top of the interface using Streamlit columns
2. WHEN processing voice input, THE Command_Center_UI SHALL track and display STT latency in milliseconds
3. WHEN generating responses, THE Command_Center_UI SHALL track and display LLM latency in milliseconds
4. WHEN synthesizing speech, THE Command_Center_UI SHALL track and display TTS latency in milliseconds
5. THE Command_Center_UI SHALL display the current model name in the dashboard
6. THE Command_Center_UI SHALL display token usage statistics for each interaction
7. THE dashboard SHALL update in real-time as new interactions occur

### Requirement 5: Live Transcription Display

**User Story:** As a user, I want to see what I said and what the agent responded in real-time, so that I can follow the conversation and verify accuracy.

#### Acceptance Criteria

1. THE Command_Center_UI SHALL replace chat bubbles with a single large Live_Transcription container
2. THE Live_Transcription container SHALL use Streamlit's st.empty() for real-time updates
3. WHEN user speech is transcribed, THE Live_Transcription SHALL display the transcribed text immediately
4. WHEN the agent generates a response, THE Live_Transcription SHALL display the response text immediately
5. THE Live_Transcription SHALL show both user and agent messages in chronological order
6. THE Live_Transcription SHALL use visual formatting to distinguish between user speech and agent responses

### Requirement 6: Dark Theme Command Center Aesthetic

**User Story:** As a user, I want a professional command center interface with high contrast, so that the system feels mission-critical and is easy to read.

#### Acceptance Criteria

1. THE Command_Center_UI SHALL implement a dark theme color scheme
2. THE Command_Center_UI SHALL use high-contrast text for readability
3. THE Command_Center_UI SHALL style metrics and status indicators to resemble a monitoring system
4. THE Command_Center_UI SHALL use visual hierarchy to emphasize critical information
5. WHEN displaying status information, THE Command_Center_UI SHALL use color coding for different states (active, processing, complete)

### Requirement 7: Voice Performance Optimization

**User Story:** As a voice interaction designer, I want responses optimized for voice delivery, so that users receive natural, complete responses without mid-sentence cutoffs.

#### Acceptance Criteria

1. THE Sentinel SHALL maintain max_output_tokens at 400 to prevent mid-sentence cutoffs
2. WHEN generating responses, THE Sentinel SHALL optimize text for conversational voice delivery
3. THE Sentinel SHALL maintain concise responses suitable for voice interaction
4. THE Voice_Handler SHALL continue using Piper TTS with en_US-lessac-medium voice
5. THE Voice_Handler SHALL continue using Faster-Whisper with the tiny model for STT
6. WHEN synthesizing speech, THE Voice_Handler SHALL enforce sentence limits to maintain response brevity

### Requirement 8: Latency Tracking Infrastructure

**User Story:** As a system administrator, I want to track processing latency at each stage, so that I can identify performance bottlenecks and optimize user experience.

#### Acceptance Criteria

1. THE Sentinel SHALL measure and record STT processing time for each voice input
2. THE Sentinel SHALL measure and record LLM response generation time for each interaction
3. THE Sentinel SHALL measure and record TTS synthesis time for each response
4. THE Sentinel SHALL store latency metrics in session state for dashboard display
5. WHEN latency exceeds acceptable thresholds, THE Sentinel SHALL log warnings for monitoring
6. THE latency tracking SHALL not significantly impact overall system performance

### Requirement 9: Conversation State Preservation

**User Story:** As a user, I want my conversation context maintained throughout the voice interaction, so that I don't have to repeat information.

#### Acceptance Criteria

1. THE Sentinel SHALL maintain the existing ConversationStateData structure
2. THE Sentinel SHALL preserve user information across voice interactions
3. THE Sentinel SHALL maintain conversation history for context in subsequent interactions
4. WHEN transitioning to escalation, THE Sentinel SHALL pass collected user information to the triage_and_escalate tool
5. THE conversation state SHALL persist throughout the voice session

### Requirement 10: Tool Response Structure Standardization

**User Story:** As a developer, I want consistent tool response structures, so that the conversation flow can reliably detect escalation conditions.

#### Acceptance Criteria

1. WHEN a tool completes successfully, THE tool SHALL return a structured response with a status field
2. WHEN a tool requires escalation, THE tool SHALL return a response with status "not_supported" and action "escalate"
3. THE tool response structure SHALL include an escalation_required boolean field
4. THE tool response SHALL be parseable by the conversation flow manager
5. WHEN multiple tools are available, THE response structure SHALL be consistent across all tools

### Requirement 11: Automatic Welcome Message on Initialization

**User Story:** As a user, I want to hear Sentinel's welcome message immediately after loading models, so that I know the system is ready and I can start interacting naturally.

#### Acceptance Criteria

1. WHEN the voice models are loaded successfully, THE Sentinel SHALL automatically generate the welcome message audio
2. WHEN the welcome message audio is ready, THE Command_Center_UI SHALL play it automatically
3. THE welcome message SHALL be "Hello! I'm Sentinel. How can I help you today?"
4. THE welcome message playback SHALL occur without requiring user interaction
5. WHEN the welcome message is playing, THE Live_Transcription SHALL display the welcome text

### Requirement 12: Legacy Code Cleanup

**User Story:** As a developer, I want to remove unused dependencies and patches, so that the codebase remains clean and maintainable.

#### Acceptance Criteria

1. THE Sentinel SHALL remove the tts_patch.py file as it is specific to XTTS and not needed for Piper TTS
2. THE Voice_Handler SHALL remove the import statement for tts_patch from streamlit_voice_handler.py
3. THE Sentinel SHALL verify that no other components depend on the TTS patch
4. THE Sentinel SHALL remove any XTTS-related configuration or dependencies if present
