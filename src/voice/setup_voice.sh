#!/bin/bash
# Voice capabilities setup script for Sentinel Insurance Agent
# Downloads and caches Whisper STT model
# Piper TTS models are included locally (en_US-lessac-medium.onnx)
# Run once: chmod +x src/voice/setup_voice.sh && ./src/voice/setup_voice.sh

set -e  # Exit on error

echo "🎙️ Sentinel Voice Setup"
echo "======================="
echo "This script will download the Whisper STT model (~150MB)"
echo "Piper TTS models are already included in src/voice/"
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    echo "Then run this script again."
    exit 1
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"
echo ""

# Check disk space
echo "Checking disk space..."
available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
required_space=1

if [ "$available_space" -lt "$required_space" ]; then
    echo "❌ Insufficient disk space (need ${required_space}GB, have ${available_space}GB)"
    exit 1
fi
echo "✅ Sufficient disk space (${available_space}GB available)"
echo ""

# Verify Piper TTS models exist locally
echo "Checking Piper TTS models..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PIPER_MODEL="$SCRIPT_DIR/en_US-lessac-medium.onnx"
PIPER_CONFIG="$SCRIPT_DIR/en_US-lessac-medium.onnx.json"

if [ ! -f "$PIPER_MODEL" ] || [ ! -f "$PIPER_CONFIG" ]; then
    echo "❌ Piper TTS models not found in $SCRIPT_DIR"
    echo "Expected files:"
    echo "  - en_US-lessac-medium.onnx"
    echo "  - en_US-lessac-medium.onnx.json"
    echo ""
    echo "Please ensure these files are present in src/voice/"
    exit 1
fi
echo "✅ Piper TTS models found"
echo "   Model: $(basename $PIPER_MODEL)"
echo "   Config: $(basename $PIPER_CONFIG)"
echo ""

# Download Whisper model
echo "📥 Downloading Whisper STT model (tiny, ~75MB)..."
echo "This may take a few minutes..."
python -c "
from faster_whisper import WhisperModel
import sys

try:
    print('Loading Whisper tiny model with int8 quantization...')
    model = WhisperModel('tiny', device='cpu', compute_type='int8')
    print('✅ Whisper model cached successfully')
    print('   Model: tiny (optimized for low latency)')
    print('   Device: CPU')
    print('   Compute type: int8')
except Exception as e:
    print(f'❌ Failed to download Whisper model: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Whisper setup failed"
    exit 1
fi
echo ""

# Test Piper TTS
echo "� Testing Piper TTS..."
python -c "
from piper import PiperVoice
from pathlib import Path
import sys

try:
    script_dir = Path('$SCRIPT_DIR')
    model_path = script_dir / 'en_US-lessac-medium.onnx'
    config_path = script_dir / 'en_US-lessac-medium.onnx.json'
    
    print(f'Loading Piper model from {model_path}...')
    voice = PiperVoice.load(str(model_path), config_path=str(config_path))
    print('✅ Piper TTS loaded successfully')
    print('   Voice: en_US-lessac-medium')
    print('   Type: Local ONNX model (no API calls)')
except Exception as e:
    print(f'❌ Failed to load Piper TTS: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Piper TTS test failed"
    exit 1
fi
echo ""

# Verify audio devices (optional - Streamlit handles audio in browser)
echo "🔊 Checking audio setup..."
echo "Note: Sentinel uses browser-based audio (microphone via Streamlit)"
echo "Server-side audio devices are not required."
echo ""

python -c "
import sys

try:
    import soundfile as sf
    print('✅ soundfile library available (for audio file processing)')
except ImportError:
    print('⚠️  soundfile not installed (optional dependency)')
    print('   Install with: pip install soundfile')

try:
    import numpy as np
    print('✅ numpy available (for audio processing)')
except ImportError:
    print('❌ numpy not installed (required)')
    sys.exit(1)
"
echo ""

# Summary
echo "✅ Voice setup complete!"
echo ""
echo "📊 Setup Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STT Model:  Whisper tiny (int8, CPU)"
echo "TTS Model:  Piper en_US-lessac-medium (local ONNX)"
echo "Cache:      ~/.cache/huggingface/ (~75MB)"
echo "Local:      src/voice/*.onnx (~50MB)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚡ Performance Expectations:"
echo "  STT Latency:  ~200-500ms (Whisper tiny)"
echo "  LLM Latency:  ~800-1200ms (Gemini 2.5 Flash)"
echo "  TTS Latency:  ~300-600ms (Piper local)"
echo "  Total:        ~1.5-2.5 seconds end-to-end"
echo ""
echo "📋 Next steps:"
echo "1. Ensure your .env file has GOOGLE_API_KEY set"
echo "2. Run: streamlit run app.py"
echo "3. Click 'INITIALIZE SPEECH MODELS' button"
echo "4. Click the glowing orb to start recording"
echo ""
echo "🔧 Troubleshooting:"
echo "- If microphone doesn't work, check browser permissions"
echo "- If models fail to load, check internet connection (first run only)"
echo "- For Piper issues, verify .onnx files exist in src/voice/"
echo "- Check logs in terminal for detailed error messages"
echo ""
echo "📚 Documentation:"
echo "- README.md for full setup instructions"
echo "- STRUGGLE_REPORT.md for architecture details"
echo "- src/voice/streamlit_voice_handler.py for implementation"
