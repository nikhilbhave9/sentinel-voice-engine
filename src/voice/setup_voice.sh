#!/bin/bash
# Voice capabilities setup script
# Downloads and caches voice models (~700MB total)
# Run once: chmod +x voice/setup_voice.sh && ./voice/setup_voice.sh

set -e  # Exit on error

echo "🎙️ Sentinel Voice Setup"
echo "======================="
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
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"
echo ""

# Check disk space
echo "Checking disk space..."
available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
required_space=2

if [ "$available_space" -lt "$required_space" ]; then
    echo "❌ Insufficient disk space (need ${required_space}GB, have ${available_space}GB)"
    exit 1
fi
echo "✅ Sufficient disk space (${available_space}GB available)"
echo ""

# Create models directory
echo "Creating models directory..."
mkdir -p models
echo "✅ Models directory created"
echo ""

# Download Whisper model
echo "📥 Downloading Whisper STT model (base, ~150MB)..."
echo "This may take a few minutes..."
python -c "
from faster_whisper import WhisperModel
import sys

try:
    print('Loading Whisper base model...')
    model = WhisperModel('base', device='cpu', compute_type='int8')
    print('✅ Whisper model cached successfully')
except Exception as e:
    print(f'❌ Failed to download Whisper model: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Whisper setup failed"
    exit 1
fi
echo ""

# Download XTTS model
echo "📥 Downloading XTTS TTS model (~500MB)..."
echo "This may take several minutes..."
python -c "
from TTS.api import TTS
import sys

try:
    print('Loading XTTS v2 model...')
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cpu')
    print('✅ XTTS model cached successfully')
except Exception as e:
    print(f'❌ Failed to download XTTS model: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ XTTS setup failed"
    exit 1
fi
echo ""

# Verify audio devices
echo "🔊 Checking audio devices..."
python -c "
import sounddevice as sd
import sys

try:
    devices = sd.query_devices()
    print('Available audio devices:')
    print(devices)
    print('')
    
    # Check for input device
    input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
    if not input_devices:
        print('⚠️  Warning: No input devices (microphones) found')
        print('   Voice input will not work without a microphone')
    else:
        print(f'✅ Found {len(input_devices)} input device(s)')
    
    # Check for output device
    output_devices = [d for d in sd.query_devices() if d['max_output_channels'] > 0]
    if not output_devices:
        print('⚠️  Warning: No output devices (speakers) found')
        print('   Voice output will not work without speakers')
    else:
        print(f'✅ Found {len(output_devices)} output device(s)')
        
except Exception as e:
    print(f'⚠️  Could not check audio devices: {e}')
    print('   Voice features may not work properly')
"
echo ""

# Summary
echo "✅ Voice setup complete!"
echo ""
echo "Models cached in: ~/.cache/huggingface/"
echo "Estimated disk usage: ~700MB"
echo ""
echo "Next steps:"
echo "1. Ensure your .env file has GOOGLE_API_KEY set"
echo "2. Run: streamlit run app.py"
echo "3. Click 'Start Call' to test voice features"
echo ""
echo "Troubleshooting:"
echo "- If microphone doesn't work, check system permissions"
echo "- If models fail to load, check internet connection"
echo "- For audio issues, run: python -c 'import sounddevice as sd; print(sd.query_devices())'"
