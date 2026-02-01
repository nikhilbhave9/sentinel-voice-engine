# Voice Capabilities Implementation Tasks

## Task 1: Dependencies & Setup

**Objective:** Install Pipecat and voice models without breaking existing functionality.

**Status:** Not Started

### Subtasks:

- [ ] 1.1 Update requirements.txt with voice dependencies
  - Add pipecat-ai[local]>=0.0.30
  - Add faster-whisper>=0.10.0
  - Add TTS>=0.22.0
  - Add pyaudio>=0.2.14
  - Add sounddevice>=0.4.6
  - Add numpy>=1.24.0

- [ ] 1.2 Install dependencies and verify
  - Run: pip install -r requirements.txt
  - Test imports: pipecat, faster_whisper, TTS, sounddevice
  - Verify no conflicts with existing packages

- [ ] 1.3 Create voice directory structure
  - Create voice/ directory
  - Create voice/__init__.py
  - Create voice/setup_voice.sh script

- [ ] 1.4 Implement setup_voice.sh script
  - Add Python version check (3.10+)
  - Add disk space check (2GB minimum)
  - Add Whisper model download logic
  - Add XTTS model download logic
  - Add audio device verification
  - Add error handling and user feedback
  - Make script executable: chmod +x voice/setup_voice.sh

- [ ] 1.5 Extend src/core/config.py with voice settings
  - Add voice_stt_model field (default: "base")
  - Add voice_stt_device field (default: "cpu")
  - Add voice_stt_compute_type field (default: "int8")
  - Add voice_tts_model field (default: "tts_models/multilingual/multi-dataset/xtts_v2")
  - Add voice_tts_language field (default: "en")
  - Add voice_tts_speed field (default: 1.0)
  - Add voice_silence_threshold field (default: 0.5)
  - Add voice_silence_duration field (default: 0.8)
  - Add voice_max_sentences field (default: 2)
  - Add voice_enabled field (default: True)

- [ ] 1.6 Update .env.example with voice configuration
  - Add voice configuration section
  - Document all voice environment variables
  - Provide example values

- [ ] 1.7 Test setup script
  - Run ./voice/setup_voice.sh on clean environment
  - Verify Whisper model downloads (~150MB)
  - Verify XTTS model downloads (~500MB)
  - Verify models cached in ~/.cache/huggingface/
  - Test audio device detection

- [ ] 1.8 Test configuration loading
  - Create test .env with voice settings
  - Verify get_settings() loads voice config
  - Test default values
  - Test environment variable overrides

**Acceptance Criteria:**
- All dependencies install without errors
- Setup script successfully downloads models
- Audio devices are detected
- Voice configuration loads correctly
- Existing text interface still works
- No breaking changes to existing code

**Testing:**
```bash
# Test dependency installation
pip install -r requirements.txt
python3 -c "import pipecat; import faster_whisper; import TTS; print('✅ All imports successful')"

# Test setup script
./voice/setup_voice.sh

# Test audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test configuration
python3 -c "from src.core.config import get_settings; s = get_settings(); print(f'Voice enabled: {s.voice_enabled}')"

# Test existing app still works
streamlit run app.py
```

**Pause Point:** Test setup, verify models downloaded, check audio devices, then commit before moving to Task 2.

---


## Task 2: Voice Processor (Business Logic Bridge)

**Objective:** Create processor that enforces voice constraints and connects Pipecat to existing Sentinel agent.

**Status:** Not Started

### Subtasks:

- [ ] 2.1 Create voice/voice_processor.py file
  - Create file with module docstring
  - Add necessary imports (pipecat, logging, re)
  - Import conversation_flow_manager and models

- [ ] 2.2 Implement SentinelVoiceProcessor class
  - Inherit from pipecat.processors.frame_processor.FrameProcessor
  - Add __init__ method accepting ConversationStateData
  - Store conversation_state reference
  - Load config via get_settings()
  - Initialize logger

- [ ] 2.3 Implement process_frame method
  - Check if frame is TextFrame
  - Extract text from frame
  - Log incoming voice input
  - Call process_message(text, conversation_state)
  - Extract response from result
  - Apply sentence limiting
  - Log outgoing voice output
  - Return TextFrame with limited response
  - Pass through non-TextFrame frames unchanged

- [ ] 2.4 Implement _limit_sentences method
  - Handle empty/None text
  - Split text on sentence boundaries (., !, ?)
  - Take first N sentences (from config.voice_max_sentences)
  - Join sentences back together
  - Log if truncation occurred
  - Return limited text

- [ ] 2.5 Add comprehensive logging
  - Log voice input received
  - Log response before limiting
  - Log response after limiting
  - Log truncation details (original vs limited sentence count)
  - Log any errors during processing

- [ ] 2.6 Add error handling
  - Wrap process_message call in try-except
  - Handle exceptions gracefully
  - Return error message as TextFrame
  - Log errors with full traceback

- [ ] 2.7 Write unit tests (tests/test_voice_processor.py)
  - Test sentence limiting with 1 sentence
  - Test sentence limiting with 2 sentences
  - Test sentence limiting with 3+ sentences (truncation)
  - Test with empty text
  - Test with None text
  - Test integration with process_message
  - Test error handling
  - Mock ConversationStateData for tests

- [ ] 2.8 Test with mock frames
  - Create mock TextFrame inputs
  - Verify correct TextFrame outputs
  - Test with various sentence counts
  - Verify conversation state updates
  - Test error scenarios

**Acceptance Criteria:**
- SentinelVoiceProcessor correctly processes TextFrames
- Responses limited to max 2 sentences
- Uses existing process_message() logic (no changes to flow manager)
- Conversation state maintained correctly
- Comprehensive logging in place
- Error handling works gracefully
- Unit tests pass with >80% coverage
- No changes to Support/Sales pathways

**Testing:**
```python
# Test sentence limiting
from voice.voice_processor import SentinelVoiceProcessor
from src.core.models import ConversationStateData
from pipecat.frames.frames import TextFrame

state = ConversationStateData()
processor = SentinelVoiceProcessor(state)

# Test with 3 sentences
text = "First sentence. Second sentence. Third sentence."
result = processor._limit_sentences(text)
assert result.count('.') <= 2

# Test with mock frame
frame = TextFrame(text="I need help with my policy")
result_frame = await processor.process_frame(frame)
assert isinstance(result_frame, TextFrame)
assert len(result_frame.text) > 0
```

**Pause Point:** Test voice processor with mock data, verify sentence limiting works, run unit tests, then commit before moving to Task 3.

---


## Task 3: Pipecat Pipeline Handler

**Objective:** Create main voice handler that orchestrates the entire STT → Agent → TTS pipeline.

**Status:** Not Started

### Subtasks:

- [ ] 3.1 Create voice/pipecat_handler.py file
  - Create file with module docstring
  - Add necessary imports (pipecat, asyncio, logging)
  - Import voice_processor, models, config

- [ ] 3.2 Implement VoicePipelineHandler class structure
  - Add __init__ method accepting ConversationStateData
  - Initialize instance variables (pipeline, runner, is_running)
  - Load config via get_settings()
  - Initialize logger

- [ ] 3.3 Implement initialize() method
  - Create LocalAudioTransport for mic + speaker
  - Configure SileroVADAnalyzer for voice activity detection
  - Configure WhisperSTTService with model settings
  - Create SentinelVoiceProcessor instance
  - Configure XTTSService with model settings
  - Build Pipeline with all components in order
  - Create PipelineRunner
  - Add comprehensive error handling
  - Log initialization success/failure

- [ ] 3.4 Implement start() method
  - Check if already running
  - Call initialize()
  - Set is_running flag
  - Start pipeline runner
  - Log start event
  - Handle initialization errors

- [ ] 3.5 Implement stop() method
  - Check if running
  - Stop pipeline runner
  - Clear pipeline and runner references
  - Set is_running to False
  - Clean up resources
  - Log stop event
  - Handle cleanup errors

- [ ] 3.6 Implement get_status() method
  - Return dictionary with current status
  - Include is_running flag
  - Include pipeline initialization status
  - Include configuration details
  - Include model loading status

- [ ] 3.7 Add latency tracking
  - Track STT processing time
  - Track LLM processing time
  - Track TTS processing time
  - Calculate total end-to-end latency
  - Log latency metrics
  - Warn if latency exceeds 2 second target

- [ ] 3.8 Add comprehensive error handling
  - Handle audio device errors
  - Handle model loading errors
  - Handle pipeline runtime errors
  - Implement graceful degradation
  - Log all errors with context

- [ ] 3.9 Write unit tests (tests/test_pipecat_handler.py)
  - Test pipeline initialization
  - Test start/stop lifecycle
  - Test status reporting
  - Test error handling
  - Mock Pipecat components for tests

- [ ] 3.10 Test end-to-end voice pipeline
  - Initialize handler with test state
  - Start pipeline
  - Test with recorded audio input
  - Verify transcription output
  - Verify agent response generation
  - Verify TTS audio output
  - Measure latency
  - Stop pipeline cleanly

- [ ] 3.11 Optimize for sub-2-second latency
  - Profile each pipeline stage
  - Identify bottlenecks
  - Optimize model loading
  - Implement concurrent processing where possible
  - Test latency under various conditions
  - Document optimization results

**Acceptance Criteria:**
- Complete pipeline initializes successfully
- Audio flows: Mic → Whisper → Processor → XTTS → Speaker
- Pipeline starts and stops cleanly
- Resources cleaned up properly on stop
- Total latency < 2 seconds (95th percentile)
- Error handling works for all failure modes
- Unit tests pass
- End-to-end test completes successfully

**Testing:**
```python
# Test pipeline lifecycle
from voice.pipecat_handler import VoicePipelineHandler
from src.core.models import ConversationStateData

state = ConversationStateData()
handler = VoicePipelineHandler(state)

# Test initialization
await handler.initialize()
assert handler.pipeline is not None
assert handler.runner is not None

# Test start
await handler.start()
assert handler.is_running == True

# Test status
status = handler.get_status()
assert status['is_running'] == True

# Test stop
await handler.stop()
assert handler.is_running == False
assert handler.pipeline is None
```

**Manual Testing:**
```bash
# Test with real audio
python3 -c "
import asyncio
from voice.pipecat_handler import VoicePipelineHandler
from src.core.models import ConversationStateData

async def test():
    state = ConversationStateData()
    handler = VoicePipelineHandler(state)
    await handler.start()
    # Speak into microphone: 'Hello, I need help'
    await asyncio.sleep(10)  # Let it process
    await handler.stop()

asyncio.run(test())
"
```

**Pause Point:** Test complete voice pipeline, measure latency, verify audio I/O works, then commit before moving to Task 4.

---


## Task 4: Streamlit Voice Interface

**Objective:** Create user-friendly voice interface in Streamlit with clear controls and status indicators.

**Status:** Not Started

### Subtasks:

- [ ] 4.1 Add voice session state initialization to app.py
  - Add initialize_voice_session_state() function
  - Initialize voice_handler (None initially)
  - Initialize voice_status ("idle")
  - Initialize voice_transcription ("")
  - Initialize voice_response ("")
  - Call from main() after existing initialization

- [ ] 4.2 Create two-column layout in main()
  - Use st.columns([1, 1]) for equal split
  - Left column: existing text chat interface
  - Right column: new voice call interface
  - Ensure both columns visible simultaneously

- [ ] 4.3 Refactor existing chat into render_text_chat_interface()
  - Move existing chat display logic to new function
  - Move chat input handling to new function
  - Keep all existing functionality intact
  - Call from left column

- [ ] 4.4 Implement render_voice_call_interface()
  - Add subheader "🎙️ Voice Call"
  - Display current status with color indicators
  - Add Start Call button
  - Add End Call button
  - Display transcription area
  - Display response area
  - Show error messages if any

- [ ] 4.5 Implement handle_start_call()
  - Set status to "initializing"
  - Create VoicePipelineHandler with current conversation_state
  - Store handler in session state
  - Start pipeline asynchronously
  - Set status to "listening" on success
  - Set status to "error" on failure
  - Display error message to user
  - Trigger UI rerun

- [ ] 4.6 Implement handle_end_call()
  - Get handler from session state
  - Stop pipeline asynchronously
  - Clear handler from session state
  - Set status to "idle"
  - Clear transcription and response
  - Trigger UI rerun
  - Handle errors gracefully

- [ ] 4.7 Add status indicators
  - Idle: 🟢 "Ready to start call"
  - Initializing: 🟡 "Initializing voice pipeline..."
  - Listening: 🔵 "Listening..."
  - Processing: 🟡 "Processing..."
  - Speaking: 🟣 "Speaking..."
  - Error: 🔴 "Error - [message]"

- [ ] 4.8 Implement real-time status updates
  - Update status during pipeline lifecycle
  - Show transcription as it arrives
  - Show response when generated
  - Update UI with st.rerun()

- [ ] 4.9 Add conversation history integration
  - Voice interactions appear in messages list
  - Format: {"role": "user", "content": transcription, "source": "voice"}
  - Format: {"role": "assistant", "content": response, "source": "voice"}
  - Display in both text and voice sections

- [ ] 4.10 Ensure state synchronization
  - Voice and text share same conversation_state
  - User info collected via voice appears in sidebar
  - Conversation flows work identically
  - State transitions synchronized

- [ ] 4.11 Add error handling UI
  - Display user-friendly error messages
  - Provide troubleshooting hints
  - Show expandable error details (optional)
  - Offer retry or fallback options

- [ ] 4.12 Test voice interface functionality
  - Test Start Call button
  - Test End Call button
  - Test status transitions
  - Test transcription display
  - Test response display
  - Test error scenarios

- [ ] 4.13 Test dual interface integration
  - Start conversation via text
  - Continue via voice
  - Switch back to text
  - Verify state maintained
  - Verify history shows both

- [ ] 4.14 Test conversation flows via voice
  - Test greeting flow
  - Test support flow (say "I need help with my policy")
  - Test sales flow (say "I want to buy insurance")
  - Verify info extraction works
  - Verify state transitions work

- [ ] 4.15 User acceptance testing
  - Test with real users
  - Gather feedback on UI/UX
  - Test on different browsers
  - Test on different screen sizes
  - Verify accessibility

- [ ] 4.16 Update README.md
  - Add voice features section
  - Document setup requirements
  - Add usage instructions
  - Add troubleshooting guide
  - Update system requirements

**Acceptance Criteria:**
- Voice interface displays correctly alongside text chat
- Start Call button initializes pipeline
- End Call button stops pipeline cleanly
- Status indicators update in real-time
- Transcriptions display correctly
- Responses display correctly
- Both interfaces share conversation state
- User info collected via voice appears in sidebar
- All conversation flows work via voice
- Error messages are clear and helpful
- UI is intuitive and responsive
- Documentation updated

**Testing:**
```python
# Manual UI testing checklist

# Test 1: Basic voice call
1. Open app: streamlit run app.py
2. Click "Start Call"
3. Verify status changes to "Listening"
4. Say: "Hello, I need help with my policy"
5. Verify transcription appears
6. Verify agent response appears
7. Verify audio plays
8. Click "End Call"
9. Verify status returns to "Idle"

# Test 2: State synchronization
1. Type in text chat: "My name is John"
2. Verify name appears in sidebar
3. Click "Start Call"
4. Say: "My policy number is ABC123456"
5. Verify policy number appears in sidebar
6. Click "End Call"
7. Continue in text chat
8. Verify conversation context maintained

# Test 3: Error handling
1. Disconnect microphone
2. Click "Start Call"
3. Verify error message displayed
4. Verify helpful troubleshooting hints
5. Reconnect microphone
6. Retry and verify success

# Test 4: Conversation flows
1. Start voice call
2. Say: "I want to buy car insurance"
3. Verify sales flow activated
4. Verify appropriate questions asked
5. Continue conversation
6. Verify state transitions work
```

**Performance Testing:**
```bash
# Measure end-to-end latency
1. Start voice call
2. Say test phrase
3. Measure time from speech end to audio playback start
4. Verify < 2 seconds
5. Repeat 10 times
6. Calculate average and 95th percentile
```

**Pause Point:** Complete UI testing, gather user feedback, verify all acceptance criteria met, then final commit.

---


## Summary

### Task Overview

| Task | Description | Estimated Time | Dependencies |
|------|-------------|----------------|--------------|
| Task 1 | Dependencies & Setup | 2-3 hours | None |
| Task 2 | Voice Processor | 3-4 hours | Task 1 |
| Task 3 | Pipecat Pipeline Handler | 4-6 hours | Task 1, Task 2 |
| Task 4 | Streamlit Voice Interface | 4-6 hours | Task 1, Task 2, Task 3 |

**Total Estimated Time:** 13-19 hours

### Critical Path

```
Task 1 (Setup)
    ↓
Task 2 (Voice Processor) ← Must complete before Task 3
    ↓
Task 3 (Pipeline Handler) ← Must complete before Task 4
    ↓
Task 4 (Streamlit UI) ← Final integration
```

### Pause Points

**After Task 1:**
- ✅ Dependencies installed
- ✅ Models downloaded
- ✅ Audio devices detected
- ✅ Configuration working
- 🎯 **Action:** Test setup, commit, then proceed

**After Task 2:**
- ✅ Voice processor implemented
- ✅ Sentence limiting works
- ✅ Unit tests pass
- 🎯 **Action:** Test with mock data, commit, then proceed

**After Task 3:**
- ✅ Complete pipeline working
- ✅ Audio I/O functional
- ✅ Latency < 2 seconds
- 🎯 **Action:** Test end-to-end, measure performance, commit, then proceed

**After Task 4:**
- ✅ UI complete
- ✅ All features working
- ✅ User testing done
- 🎯 **Action:** Final testing, documentation, deploy

### Success Metrics

**Functional:**
- [ ] Voice call starts successfully
- [ ] Speech transcribed accurately
- [ ] Agent responds appropriately
- [ ] Audio output clear and natural
- [ ] Call ends cleanly
- [ ] State synchronized between text/voice

**Performance:**
- [ ] Total latency < 2 seconds (95th percentile)
- [ ] STT latency < 1 second
- [ ] LLM latency < 1 second
- [ ] TTS latency < 1 second
- [ ] Memory usage < 3GB

**Quality:**
- [ ] No breaking changes to text interface
- [ ] Error handling comprehensive
- [ ] Resource cleanup complete
- [ ] Logging comprehensive
- [ ] Unit test coverage > 80%
- [ ] Documentation complete

### Risk Mitigation

**Risk: Model download failures**
- Mitigation: Retry logic in setup script, clear error messages

**Risk: Audio device issues**
- Mitigation: Device detection, permission handling, troubleshooting guide

**Risk: Latency exceeds target**
- Mitigation: Profiling, optimization, concurrent processing

**Risk: Memory constraints**
- Mitigation: Model optimization (int8), lazy loading, monitoring

**Risk: Breaking existing features**
- Mitigation: No changes to core logic, comprehensive testing, gradual rollout

### Next Steps After Completion

1. **Monitoring:** Set up latency and error tracking
2. **Optimization:** Profile and optimize based on real usage
3. **User Feedback:** Gather feedback and iterate
4. **Documentation:** Create user guides and troubleshooting docs
5. **Phase 2:** Consider barge-in, multi-language, GPU acceleration

---

## Notes

- **IMPORTANT:** Pause after each task for testing and review
- **IMPORTANT:** Commit after each task completion
- **IMPORTANT:** Do not proceed to next task until current task is verified working
- **IMPORTANT:** If tests fail, fix issues before moving forward
- **IMPORTANT:** Keep existing text interface fully functional throughout

---

**Tasks Document Version:** 1.0  
**Created:** 2026-02-01  
**Status:** Ready for Implementation
