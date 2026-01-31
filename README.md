# 🛡️ Sentinel Insurance Agent - Simplified

A streamlined conversational AI insurance agent built with Streamlit and Google Gemini. This simplified version provides intelligent customer support for insurance inquiries through a clean, maintainable codebase.

## ✨ Features

- **🤖 AI-Powered Conversations**: Natural language processing using Google Gemini
- **💬 Clean Chat Interface**: Simple chat UI with conversation history
- **📊 Session Management**: Conversation state maintained during browser session
- **🎯 Conversation Flow Management**: Intelligent routing between support and sales flows
- **🔧 Simple Configuration**: Easy setup with environment variables

## 🚀 Quick Start

### Prerequisites
- **Python 3.8 or higher**
- **Google Gemini API key** ([Get your free API key](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd sentinel-insurance-agent
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your Google Gemini API key
```

5. **Launch the application:**
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 📖 How to Use

### Getting Started
1. Launch the application using `streamlit run app.py`
2. Open your browser to `http://localhost:8501`
3. Start chatting with Sentinel using the input box

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

## ⚙️ Configuration

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

## 📁 Project Structure

```
sentinel-insurance-agent/
├── app.py                           # Main Streamlit application
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Your environment variables (create this)
├── README.md                       # This file
├── notes.md                        # Development notes
└── src/                           # Source code
    ├── core/
    │   ├── config.py               # Configuration management
    │   ├── conversation_flow_manager.py  # Conversation logic
    │   ├── models.py               # Data models
    │   ├── prompts.py              # AI prompts
    │   └── tools.py                # Function tools
    └── integration/
        └── gemini_client.py        # Google Gemini API client
```

## 🚨 Troubleshooting

### Common Issues

**1. "Configuration error" or API key issues**
- Ensure your `.env` file exists in the project root
- Verify your `GEMINI_API_KEY` is correctly set
- Check that your API key starts with "AIza"
- Get a new API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

**2. "Module not found" errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check if you're in the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Application won't start**
```bash
# Check Python version (3.8+ required)
python --version

# Try running with explicit Python path
python -m streamlit run app.py
```

**4. "Port already in use" error**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

**5. AI responses not working**
- Check your internet connection
- Verify your API key is active and has quota remaining
- Try refreshing the page to restart the session

### Getting Help

1. Check the browser console for error messages
2. Verify all files are present in the project structure
3. Ensure your `.env` file has the correct format
4. Try creating a fresh virtual environment

## 🛠️ Development

This is a simplified version of the Sentinel Insurance Agent, focusing on core functionality with minimal complexity.

### Key Design Principles
- **Simplicity**: Minimal file structure and dependencies
- **Maintainability**: Clear separation of concerns
- **Functionality**: All essential features preserved
- **Streamlit-native**: Uses built-in session state management

### File Count: 9 Core Files
1. `app.py` - Main application
2. `src/core/config.py` - Configuration
3. `src/core/conversation_flow_manager.py` - Conversation logic
4. `src/core/models.py` - Data models
5. `src/core/prompts.py` - AI prompts
6. `src/core/tools.py` - Function tools
7. `src/integration/gemini_client.py` - API client
8. `requirements.txt` - Dependencies
9. `README.md` - Documentation

---

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Google Gemini**: For the AI language model
- **Streamlit**: For the web application framework

---

**🛡️ Sentinel Insurance Agent** - Simplified AI insurance assistance