# Sentinel Insurance Agent

A conversational logic engine built with Streamlit and powered by Google Gemini LLM models. This agent provides intelligent customer support for insurance inquiries (either new sales inquiry or support for existing customer)

## Quick Start

### Prerequisites
- **Python 3.11**
- **Google Gemini API key** ([Get API key](https://aistudio.google.com/app/))

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd sentinel-insurance-agent
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables using the example env file**
```bash
cp .env.example .env
```

5. **Launch the application:**
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## How to Use

### Getting Started
1. Launch the application using `streamlit run app.py`
2. Open your browser to `http://localhost:8501`
3. Click on the Initialize Models button (5-7 seconds)
4. Start speaking by toggling the orb button (you will be able to view the transcript on the side)

### Conversation Flows

**🏠 Greeting Flow**
- Sentinel starts with a friendly greeting
- Ask general questions about insurance

**🛠️ Support Flow**
- Say "I need help with my policy" or similar
- Get assistance with claims and coverage questions

**💼 Sales Flow**
- Say "I'm interested in insurance" or "I want to buy coverage"
- Discuss your insurance needs and get policy information

### Sample Conversation

Here's an example of a typical sales conversation with Sentinel:

```
[SENTINEL] Hello! I'm Sentinel. How can I help you today?

[USER] Hi, my name is Bob. I want a new fire insurance policy.

[SENTINEL] Hi Bob! I can definitely help you with a new home insurance policy. 
Could you please share your phone number so I can check for available consultation slots?

[USER] Sure. My phone number is 11111111111111.

[SENTINEL] Great! Thanks, Bob. I see a few open slots for a home insurance consultation: 
Monday at 10:00 AM, Tuesday at 2:00 PM, and Wednesday at 4:30 PM. 
Which of these works best for you?

[USER] Monday at 10 AM works best for me.

[SENTINEL] Great! Your appointment for a fire insurance consultation on Monday at 10:00 AM 
has been booked.
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | `AIza...` |
| `GEMINI_MODEL_NAME` | ❌ | AI model to use | `gemini-1.5-flash` |
| `GEMINI_TEMPERATURE` | ❌ | Response creativity (0.0-2.0) | `0.7` |
| `GEMINI_MAX_TOKENS` | ❌ | Max response length | `150` |

### Example .env file:
```bash
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=150
```

## Project Structure

```
sentinel-voice-engine/
├── app.py                           # Main Streamlit application
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Your environment variables (create this)
├── README.md                       # This file
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── .kiro/                          # Kiro AI specs and workflows
│   ├── specs/                      # Feature specifications
│   └── hooks/                      # Automation hooks
└── src/                           # Source code
    ├── core/
    │   ├── config.py               # Configuration management
    │   ├── conversation_flow_manager.py  # Conversation logic
    │   ├── metrics.py              # Performance tracking
    │   ├── models.py               # Data models
    │   ├── prompts.py              # AI prompts
    │   └── tools.py                # Function tools
    ├── integration/
    │   └── gemini_client.py        # Google Gemini API client
    └── voice/
        ├── streamlit_voice_handler.py  # Voice processing handler
        ├── voice_processor.py      # Voice utilities
        ├── en_US-lessac-medium.onnx    # Piper TTS model
        ├── en_US-lessac-medium.onnx.json  # Model config
        ├── en_US-lessac-low.onnx   # Lightweight TTS model
        ├── en_US-lessac-low.onnx.json  # Model config
        └── setup_voice.sh          # Voice setup script
```

## The "Struggle" Report

### What the agent does well
- The Speech-to-Text (STT) component is very fast, due to "tiny" Whisper model. 
- The Piper TTS is also a local ONNX-based TTS model that can usually generate speech in 500-600ms
- The conversation context is persisted across reruns using Streamlit session state dict (with keys like `messages`, `conversation_state`, `last_audio_hash`, etc.) combined with the `build_context()` function that takes a snapshot of the LLM's current history along with the cumulatively collected user info. 
- Tool calls are passed directly to the LLM model (in this project, through Gemini's new genai API), which then decides when to call it. Depending on the strenght of the model, this reduces brittleness as there is no need to exhaustively hard-code all corner cases.   

### Where the agent struggles
- The "tiny" Whisper STT model sacrifices accuracy for speed. Unless the user speaks moderately slow, at a consistent pace, the model is likely to miss a couple of words or get the spelling wrong. 
- Despite multiple mitigation strategies, the agent sometimes generates verbose responses that are awkward when spoken aloud.
- The policy detection logic was a bit brittle, which needed an additional layer of complexity to be added via the `normalize_policy_number()` function. This is not very scalable and needs a more robust solution.
- When escalation is triggered, the conversation flow can feel abrupt.

### Improvements made
- To enforce a 2-3 second "conversational" tone of the agent, I tried using an 80 token limit on the max-output. Responses were cutting off mid-sentence, as this max-output tokens parameter doesn't factor into the response generation.  Identified FinishReason.MAX_TOKENS through the response object and increased the limit to 400, while adding a BREVITY_MESSAGE to every system prompt to ensure conciseness (more on this below). 
- Another tradeoff can be to upgrade to a better model like the "small" Whisper model which is more accurate (while sacrificing some speed in return).
- Lastly, LLM input can be considered in the intent decision itself (at the cost of more token usage). Right now, it is largely hardcoded through regex patterns. 

### Architectural decisions
- Different prompts for 3 main intent states: greeting, support_flow, sales_flow. Reasoning behind this was to reduce prompt complexity and thereby provide targetted behavior
- Injecting structured context into user message rather than system prompt since Gemini's automatic function calling works better with context in user message
- A common BREVITY_MESSAGE was used to enforce brevity and clarity across all intent system prompts. 
- All tools return dictionaries with `status`, `action`, `escalation_required`, `data`, `message`
- Explicit "action nudges" were introduced to avoid "thinking out loud" behaviour and facilitate decisive action
- Escalation-First Design so that tools explicitly signal when escalation is needed rather than trying to handle everything (also ensuring lesser liability)
- Pipecat was considered as an option but the added complexity wasn't justified for this use case.
