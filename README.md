# Sentinel Insurance Agent - Stage 1

A text-based conversational AI insurance agent built with Streamlit and Google Gemini LLM.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Google Gemini API key.

4. Run the application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Project Structure

```
sentinel-insurance-agent/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .streamlit/           # Streamlit configuration
│   └── config.toml
├── src/                  # Source code
│   ├── components/       # UI components
│   └── core/            # Core logic
└── tests/               # Test files
```

## Development

This is Stage 1 of the Sentinel Insurance Agent, focusing on establishing the basic conversational interface foundation.