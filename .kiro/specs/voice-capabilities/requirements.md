# Voice Capabilities for Sentinel Insurance Agent

## Overview
Add production-ready voice interaction capabilities to the Sentinel Insurance agent using the Pipecat framework with local STT/TTS models for fast, cost-effective voice conversations.

## User Stories

### US-1: Voice Call Initiation
**As a** user  
**I want to** start a voice call with the insurance agent  
**So that** I can interact naturally using speech instead of typing

**Acceptance Criteria:**
1.1. User can click a "Start Call" button in the Streamlit interface  
1.2. System initializes microphone access with proper permissions  
1.3. System displays clear status indicator showing call is active  
1.4. System provides visual feedback when listening to user speech  
1.5. Call initialization completes within 3 seconds

### US-2: Speech-to-Text Processing
**As a** user  
**I want** my spoken words to be accurately transcribed  
**So that** the agent understands my insurance questions

**Acceptance Criteria:**
2.1. System uses Faster-Whisper (base model) for local STT processing  
2.2. Transcription accuracy is sufficient for insurance domain conversations  
2.3. System handles natural speech patterns (pauses, filler words)  
2.4. STT processing latency is under 1 second for typical utterances  
2.5. System provides visual feedback showing transcribed text

### US-3: Agent Response Generation
**As a** user  
**I want** the agent to respond to my voice input with relevant information  
**So that** I can get help with my insurance needs through voice

**Acceptance Criteria:**
3.1. System uses existing Gemini LLM integration for response generation  
3.2. Agent responses are limited to maximum 2 sentences per turn  
3.3. Responses maintain context from existing conversation flow manager  
3.4. Support and Sales pathways work identically to text interface  
3.5. Response generation completes within 1 second

### US-4: Text-to-Speech Output
**As a** user  
**I want** to hear the agent's responses in natural-sounding speech  
**So that** I can have a conversational experience

**Acceptance Criteria:**
4.1. System uses XTTS v2 model for local TTS processing  
4.2. Voice output sounds natural and professional  
4.3. Speech is clear and at appropriate volume  
4.4. TTS processing latency is under 1 second  
4.5. Audio playback is smooth without stuttering or artifacts

### US-5: End-to-End Latency
**As a** user  
**I want** fast responses during voice conversations  
**So that** the interaction feels natural and responsive

**Acceptance Criteria:**
5.1. Total latency (STT → LLM → TTS) is under 2 seconds for typical exchanges  
5.2. System prioritizes speed over maximum quality  
5.3. Latency is measured and logged for monitoring  
5.4. System handles concurrent processing where possible  
5.5. Performance degrades gracefully under load

### US-6: Call Termination
**As a** user  
**I want** to end the voice call when I'm done  
**So that** I can control the conversation duration

**Acceptance Criteria:**
6.1. User can click "End Call" button to terminate  
6.2. System cleanly releases microphone and audio resources  
6.3. Conversation history is preserved after call ends  
6.4. System displays clear status showing call has ended  
6.5. User can start a new call after ending previous one

### US-7: Voice Interface Controls
**As a** user  
**I want** clear visual controls and status indicators  
**So that** I understand the current state of the voice interaction

**Acceptance Criteria:**
7.1. Interface shows distinct states: idle, listening, processing, speaking  
7.2. Microphone status is clearly visible  
7.3. Audio output status is clearly visible  
7.4. Error states are communicated clearly  
7.5. Controls are accessible and intuitive

### US-8: Dual Interface Support
**As a** user  
**I want** both text and voice interfaces available  
**So that** I can choose my preferred interaction method

**Acceptance Criteria:**
8.1. Text chat interface remains fully functional  
8.2. Voice interface is added as separate section  
8.3. Both interfaces share same conversation state  
8.4. User can switch between interfaces seamlessly  
8.5. Conversation history shows both text and voice interactions

## Technical Requirements

### TR-1: Dependencies and Setup
- Install Pipecat framework (pipecat-ai[local]>=0.0.30)
- Install Faster-Whisper (>=0.10.0) for STT
- Install TTS (>=0.22.0) for XTTS v2
- Install audio I/O libraries (pyaudio, sounddevice, numpy)
- Create setup script for one-time model downloads (~700MB total)
- Models cached locally in ~/.cache/huggingface/

### TR-2: Configuration Management
- Add voice-related settings to src/core/config.py
- Configure STT model (Faster-Whisper base, CPU, int8)
- Configure TTS model (XTTS v2, multilingual)
- Configure voice speed and silence detection thresholds
- Configure max sentence limit (2 sentences)
- All settings accessible via environment variables

### TR-3: Voice Processor Architecture
- Create voice/voice_processor.py as Pipecat processor
- Bridge between Pipecat pipeline and existing agent logic
- Enforce 2-sentence maximum constraint
- Use existing conversation_flow_manager.process_message()
- Maintain conversation state consistency
- No modifications to Support/Sales pathways

### TR-4: Pipecat Pipeline
- Create voice/pipecat_handler.py for pipeline orchestration
- Pipeline flow: Microphone → Whisper → Voice Processor → XTTS → Speaker
- Handle audio input/output streams
- Manage pipeline lifecycle (start, stop, error handling)
- Implement proper resource cleanup

### TR-5: Streamlit Integration
- Create voice interface in app.py
- Add Start Call / End Call buttons
- Display real-time status indicators
- Show transcribed text and agent responses
- Integrate with existing session state
- Preserve conversation history across interfaces

### TR-6: Performance Optimization
- Use CPU-optimized models (int8 quantization for Whisper)
- Implement concurrent processing where possible
- Minimize model loading overhead
- Cache models in memory during active calls
- Monitor and log latency metrics

### TR-7: Error Handling
- Handle microphone permission errors
- Handle audio device unavailability
- Handle model loading failures
- Provide clear error messages to users
- Implement graceful degradation
- Log errors for debugging

### TR-8: Testing and Validation
- Test audio device detection
- Verify model downloads and caching
- Test end-to-end voice pipeline
- Measure and validate latency requirements
- Test conversation state consistency
- Verify resource cleanup on call termination

## Constraints

### Hard Constraints
- Maximum 2 sentences per agent response (enforced in voice processor)
- Sub-2-second total latency requirement
- Local models only (no external API costs beyond Gemini)
- Must use existing agent.process_message() logic
- No changes to Support/Sales conversation flows
- Must work on standard hardware (CPU-only)

### Soft Constraints
- Prefer speed over maximum quality
- Minimize memory footprint
- Graceful degradation on slower hardware
- Clear user feedback at all stages
- Professional voice quality

## Out of Scope

- Real-time interruption handling (barge-in)
- Multi-language support (English only initially)
- Voice authentication or speaker identification
- Background noise cancellation beyond model defaults
- Mobile device support
- WebRTC or browser-based voice
- Voice activity detection tuning
- Custom voice training or fine-tuning

## Dependencies

### External Dependencies
- Pipecat framework for voice pipeline orchestration
- Faster-Whisper for speech-to-text
- XTTS v2 for text-to-speech
- PyAudio/SoundDevice for audio I/O
- Existing Gemini integration for LLM

### Internal Dependencies
- src/core/conversation_flow_manager.py (existing)
- src/core/config.py (to be extended)
- src/integration/gemini_client.py (existing)
- app.py (to be extended)

## Success Metrics

- Voice call can be initiated within 3 seconds
- STT transcription latency < 1 second
- LLM response generation < 1 second
- TTS synthesis latency < 1 second
- Total end-to-end latency < 2 seconds
- Conversation state consistency: 100%
- Resource cleanup success rate: 100%
- User can complete full insurance inquiry via voice

## Risks and Mitigations

### Risk: Model download failures
**Mitigation:** Provide clear setup script with error handling and retry logic

### Risk: Audio device compatibility issues
**Mitigation:** Implement device detection and provide troubleshooting guidance

### Risk: Latency exceeds 2-second target
**Mitigation:** Use optimized models (int8), concurrent processing, and performance monitoring

### Risk: Memory constraints on lower-end hardware
**Mitigation:** Use CPU-optimized models, implement lazy loading, provide system requirements

### Risk: Breaking existing text interface
**Mitigation:** Maintain separate voice module, comprehensive testing, gradual integration

## Implementation Phases

### Phase 1: Dependencies & Setup (TASK 1)
- Install all required packages
- Create model download script
- Add voice configuration to config.py
- Test model loading and caching

### Phase 2: Voice Processor (TASK 2)
- Create voice_processor.py
- Implement 2-sentence constraint
- Bridge to existing agent logic
- Test with mock audio

### Phase 3: Pipecat Pipeline (TASK 3)
- Create pipecat_handler.py
- Implement full STT → Agent → TTS pipeline
- Test end-to-end voice flow
- Measure and optimize latency

### Phase 4: Streamlit Interface (TASK 4)
- Add voice controls to app.py
- Implement status indicators
- Integrate with session state
- Test dual interface support
- User acceptance testing
