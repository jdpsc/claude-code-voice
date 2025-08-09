# Claude Code Voice Integration

Add voice-to-text capabilities to Claude Code using OpenAI Whisper for speech recognition.

## Features

- 🎤 **Push-to-Talk Recording** - Customizable hotkey (default: Right Shift)
- 📋 **Auto-Clipboard Copy** - Transcribed text automatically copied for easy pasting
- 🎯 **Local Processing** - Complete privacy with local Whisper transcription
- ⚡ **Non-Intrusive** - Claude Code runs normally with voice as background assistant
- 🔇 **Smart Silence Detection** - Auto-stops recording after silence
- 📊 **Real-time Audio Levels** - Visual feedback while recording

## Installation

### Requirements

- Python 3.9+
- macOS/Linux
- Microphone access
- Claude Code CLI installed

### System Dependencies

#### macOS
```bash
brew install portaudio ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg
```

### Setup

1. **Create virtual environment and install dependencies:**
   ```bash
   uv venv claude-voice-env
   uv pip install -r requirements.txt --python claude-voice-env/bin/python
   ```

2. **Configure voice settings:**
   ```bash
   ./claude-voice --configure-voice
   ```

### Global Installation

```bash
chmod +x install.sh
# Add ~/.local/bin to PATH
./install.sh
```

### Uninstall
```bash
chmod +x uninstall.sh
./uninstall.sh
```

## Usage

### Start Session
```bash
claude-voice
```

### Voice Input Workflow

1. **Start Recording**: Hold your PTT key (default: Right Shift)
2. **Speak**: Talk naturally, audio levels show in real-time
3. **Stop Recording**: Release PTT key or stay silent (auto-stops after 1.5s)
4. **Auto-copy**: Transcribed text copied to clipboard automatically
5. **Paste**: Press Cmd+V (or Ctrl+V) in Claude

```
🎤 Speak → 📋 Auto-copy → Cmd+V Paste → 🚀 Claude responds
```

### Example Session

```bash
claude-voice

Claude Code with Voice Support
========================================
🎙️ Voice input enabled! Press right_shift to speak
Starting Claude Code...

# Hold Right Shift and say: "analyze the main.py file"
🎤 Recording... (Release key or stay silent to stop)
  Level: ████████████░░░░░░░░░░░░░░░░░░ 2847

🎤 Voice transcribed: analyze the main.py file
📋 Copied to clipboard! Just paste into Claude (Cmd+V)

# Just paste (Cmd+V) into Claude and it processes normally
```

## Configuration Options

### Push-to-Talk Keys
- `right_shift` - Default, convenient single-key PTT ⭐
- `f13` - If you have function keys beyond F12
- `caps_lock` - Repurpose caps lock
- `left_shift` - Alternative shift key

### Whisper Models
- `tiny` - Fastest, lowest accuracy (39M parameters)
- `base` - Good balance (74M parameters) ⭐ Recommended
- `small` - Better accuracy (244M parameters)
- `medium` - High accuracy (769M parameters)
- `large` - Best accuracy (1550M parameters)

### Silence Settings
- **Duration**: How long to wait for silence before auto-stopping
  - `0.5s` - Quick stops, sensitive to pauses
  - `1.5s` - Default, allows natural pauses ⭐
  - `3.0s` - Slower stops, good for thinking pauses
- **Threshold**: Audio level sensitivity (lower = more sensitive)
  - `50` - Very sensitive (quiet environments)
  - `100` - Balanced ⭐ Recommended  
  - `200` - Less sensitive (noisy environments)
  - `500` - Much less sensitive (very noisy)

## Tips & Best Practices

- **Speak Clearly**: Enunciate commands clearly
- **Quiet Environment**: Reduces false transcriptions
- **Consistent Distance**: Keep consistent distance from microphone
- **Command Patterns**: Use consistent phrasing for common commands
- **Shortcuts**: Create aliases for frequently used voice commands

## Privacy & Security

This implementation provides complete privacy and security:
- All audio processing happens locally on your machine
- No data is sent to external servers
- Complete privacy of your voice and code
- Perfect for sensitive development environments