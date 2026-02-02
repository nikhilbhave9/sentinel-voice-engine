"""
TTS Library Patch for PyTorch 2.6 Compatibility

PyTorch 2.6 changed torch.load to use weights_only=True by default for security.
The TTS library's XTTS model checkpoints contain custom classes that need to be
allowlisted. This patch adds the necessary safe globals before loading TTS models.

This should be imported BEFORE importing TTS.api.TTS.
"""

import torch.serialization

# Add TTS classes to safe globals for torch.load
# These are the classes used in XTTS model checkpoints
try:
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    
    # Register as safe globals
    torch.serialization.add_safe_globals([
        XttsConfig,
        XttsAudioConfig,
    ])
    
    print("✅ TTS classes registered as safe globals for PyTorch 2.6")
    
except ImportError as e:
    print(f"⚠️  Could not import TTS classes for safe globals: {e}")
    print("   TTS may not be installed yet. Run: pip install TTS")
