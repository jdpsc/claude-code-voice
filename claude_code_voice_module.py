#!/usr/bin/env python3
"""
Claude Code Voice-to-Text Module
Adds push-to-talk voice input capabilities using Whisper
"""

import os
import sys
import time
import json
import wave
import queue
import threading
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

import pyaudio
import numpy as np
import pynput.keyboard
import whisper
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.text import Text

# Local Whisper only - no API dependencies needed
    
@dataclass
class VoiceConfig:
    """Configuration for voice input"""
    push_to_talk_key: str = "right_shift"  # Default PTT key
    whisper_model: str = "base"  # tiny, base, small, medium, large
    language: str = "en"  # English by default
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    silence_threshold: float = 100  # RMS threshold for silence detection
    silence_duration: float = 1.5  # Seconds of silence to stop recording
    max_recording_time: float = 30.0  # Maximum recording duration
    auto_submit: bool = False  # Auto-submit after transcription
    show_audio_levels: bool = True  # Show audio level indicator
    
    @classmethod
    def from_file(cls, config_path: Path) -> "VoiceConfig":
        """Load configuration from file"""
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
                # Remove deprecated fields if they exist
                data.pop('whisper_mode', None)
                data.pop('api_key', None)
                return cls(**data)
        return cls()
    
    def save(self, config_path: Path):
        """Save configuration to file"""
        data = self.__dict__.copy()
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)


class AudioRecorder:
    """Handles audio recording with push-to-talk"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.frames = []
        self.audio_queue = queue.Queue()
        self.console = Console()
        
    def get_audio_level(self, data: bytes) -> float:
        """Calculate RMS audio level"""
        try:
            audio_data = np.frombuffer(data, dtype=np.int16)
            if len(audio_data) == 0:
                return 0.0
            rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
            return float(rms) if not np.isnan(rms) and not np.isinf(rms) else 0.0
        except Exception:
            return 0.0
    
    def draw_audio_level(self, level: float, max_level: float = 5000) -> str:
        """Create visual audio level indicator"""
        normalized = min(level / max_level, 1.0)
        bar_length = 30
        filled = int(bar_length * normalized)
        
        if normalized < 0.3:
            color = "green"
        elif normalized < 0.7:
            color = "yellow"
        else:
            color = "red"
            
        bar = f"[{color}]{'█' * filled}{'░' * (bar_length - filled)}[/{color}]"
        return bar
    
    def record_audio(self) -> Optional[bytes]:
        """Record audio while PTT key is held"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size
        )
        
        self.frames = []
        self.recording = True
        silence_start = None
        start_time = time.time()
        min_data_threshold = 5  # Wait for at least 5 chunks before showing levels
        
        self.console.print("\n[yellow]🎤 Recording... (Release key or stay silent to stop)[/yellow]")
        
        try:
            while self.recording:
                # Check if we've exceeded max recording time
                if time.time() - start_time > self.config.max_recording_time:
                    self.console.print("[red]Max recording time reached[/red]")
                    break
                
                # Read audio chunk
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
                
                # Calculate audio level (always needed for silence detection)
                level = self.get_audio_level(data)
                
                # Only show audio levels after sufficient data
                if len(self.frames) >= min_data_threshold and self.config.show_audio_levels:
                    level_bar = self.draw_audio_level(level)
                    sys.stdout.write(f"\r  Level: {level_bar} {int(level):5d}")
                    sys.stdout.flush()
                
                # Detect silence for auto-stop
                if level < self.config.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > self.config.silence_duration:
                        self.console.print("\n[dim]Silence detected, stopping...[/dim]")
                        break
                else:
                    silence_start = None
                
                # Check if recording should continue (controlled by VoiceInput)
                if not getattr(self, 'should_continue_recording', True):
                    break
                    
        finally:
            stream.stop_stream()
            stream.close()
            if self.config.show_audio_levels:
                sys.stdout.write("\r" + " " * 50 + "\r")  # Clear the level bar
            
        if self.frames:
            return b''.join(self.frames)
        return None


class WhisperTranscriber:
    """Handles transcription using Whisper"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.console = Console()
        self.model = None
        self._load_local_model()
            
    def _load_local_model(self):
        """Load local Whisper model"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Loading Whisper model ({self.config.whisper_model})...", 
                total=None
            )
            self.model = whisper.load_model(self.config.whisper_model)
            progress.update(task, completed=True)
    
    def transcribe_local(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using local Whisper model"""
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            wf = wave.open(tmp_file.name, 'wb')
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_data)
            wf.close()
            
            # Transcribe
            result = self.model.transcribe(
                tmp_file.name,
                language=self.config.language,
                fp16=False
            )
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return result["text"].strip()
    
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data using local Whisper model"""
        if not audio_data:
            return None
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Transcribing...", total=None)
            text = self.transcribe_local(audio_data)
            progress.update(task, completed=True)
            
        return text


class VoiceInput:
    """Main voice input handler for Claude Code"""
    
    def __init__(self, config_path: Optional[Path] = None):
        # Load configuration
        if config_path is None:
            config_path = Path.home() / ".claude" / "voice_config.json"
        
        self.config = VoiceConfig.from_file(config_path)
        self.recorder = AudioRecorder(self.config)
        self.transcriber = WhisperTranscriber(self.config)
        self.console = Console()
        self.active = False
        self.listener = None
        self.recording = False
        
    def start(self, on_text: Callable[[str], None]):
        """Start voice input system"""
        self.active = True
        self.on_text = on_text
        
        # Show startup message
        self.console.print(Panel.fit(
            f"[green]Voice Input Active[/green]\n"
            f"Push-to-Talk: [yellow]{self.config.push_to_talk_key}[/yellow]\n"
            f"Model: {self.config.whisper_model}",
            title="🎙️ Voice Mode"
        ))
        
        # Start keyboard listener for PTT
        self.listener = pynput.keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
        
    def _matches_hotkey(self, key):
        """Check if key matches the configured hotkey"""
        hotkey = self.config.push_to_talk_key.lower()
        
        # Handle simple key names
        if hasattr(key, 'char') and key.char:
            return key.char.lower() == hotkey
        
        # Handle special keys
        if hasattr(key, 'name'):
            key_name = key.name.lower()
            return key_name == hotkey or hotkey.endswith(key_name)
        
        return False
    
    def _on_key_press(self, key):
        """Handle key press events"""
        if not self.active or self.recording:
            return
            
        if self._matches_hotkey(key):
            self.recording = True
            threading.Thread(target=self._record_and_transcribe, daemon=True).start()
    
    def _on_key_release(self, key):
        """Handle key release events"""
        if self._matches_hotkey(key):
            self.recording = False
            # Signal the recorder to stop
            if hasattr(self.recorder, 'should_continue_recording'):
                self.recorder.should_continue_recording = False
    
    def _record_and_transcribe(self):
        """Record audio and transcribe in a separate thread"""
        # Set up recording control
        self.recorder.should_continue_recording = True
        
        # Record audio
        audio_data = self.recorder.record_audio()
        
        if audio_data:
            # Transcribe
            text = self.transcriber.transcribe(audio_data)
            
            if text:
                # Display transcription
                self.console.print(f"\n[cyan]📝 Transcribed:[/cyan] {text}")
                
                # Ask for confirmation unless auto-submit is enabled or integration handles it
                if self.config.auto_submit or getattr(self, 'integration_mode', False):
                    self.on_text(text)
                else:
                    if Confirm.ask("[yellow]Send this command?[/yellow]", default=True):
                        self.on_text(text)
                    else:
                        self.console.print("[dim]Cancelled[/dim]")
            else:
                self.console.print("[red]Failed to transcribe audio[/red]")
    
    def stop(self):
        """Stop voice input system"""
        self.active = False
        if self.listener:
            self.listener.stop()


# Note: ClaudeCodeVoiceIntegration class removed - using wrapper approach instead
            

# Configuration CLI
def configure_voice():
    """Interactive configuration for voice settings"""
    console = Console()
    config_path = Path.home() / ".claude" / "voice_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = VoiceConfig.from_file(config_path)
    
    console.print("[bold]Claude Code Voice Configuration[/bold]\n")
    
    # Configure PTT key
    console.print("Current PTT key: [yellow]" + config.push_to_talk_key + "[/yellow]")
    console.print("Press your desired PTT key...")
    
    captured_key = None
    
    def on_key_press(key):
        nonlocal captured_key
        if hasattr(key, 'char') and key.char:
            captured_key = key.char
        elif hasattr(key, 'name'):
            captured_key = key.name
        return False  # Stop listener
    
    listener = pynput.keyboard.Listener(on_press=on_key_press)
    listener.start()
    listener.join()  # Wait for key press
    
    if captured_key:
        config.push_to_talk_key = captured_key
        console.print(f"PTT key set to: [green]{captured_key}[/green]")
    else:
        console.print("[red]Failed to capture key[/red]")
    
    # Configure language
    console.print(f"\nLanguage (current: {config.language}):")
    console.print("Common options: en, es, fr, de, it, pt, ru, ja, ko, zh, etc.")
    console.print("Use 'auto' for automatic detection or ISO 639-1 language codes")
    try:
        language_input = input("Language code: ").strip() or config.language
        config.language = language_input
        console.print(f"Language set to: [green]{language_input}[/green]")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Configuration cancelled[/red]")
        sys.exit(1)
    
    # Configure Whisper model size
    console.print("\nWhisper Model Size (tiny/base/small/medium/large):")
    console.print("- tiny: Fastest, lowest accuracy")
    console.print("- base: Good balance (recommended)")
    console.print("- small: Better accuracy")
    console.print("- medium: High accuracy")
    console.print("- large: Best accuracy")
    try:
        model_input = input("Model: ").strip() or "base"
        config.whisper_model = model_input
        
        # Configure silence duration
        console.print(f"\nSilence Duration (current: {config.silence_duration}s):")
        console.print("- 0.5: Quick stops, sensitive to pauses")
        console.print("- 1.5: Default, allows natural pauses")
        console.print("- 3.0: Slower stops, good for thinking pauses")
        
        silence_input = input("Silence duration (seconds): ").strip()
        if silence_input:
            try:
                config.silence_duration = float(silence_input)
            except ValueError:
                console.print("[yellow]Invalid input, keeping current setting[/yellow]")
        
        # Configure silence threshold
        console.print(f"\nSilence Threshold (current: {config.silence_threshold}):")
        console.print("- 50: Very sensitive (quiet environments)")
        console.print("- 100: Balanced (default)")
        console.print("- 200: Less sensitive (noisy environments)")
        console.print("- 500: Much less sensitive (very noisy)")
        
        threshold_input = input("Silence threshold: ").strip()
        if threshold_input:
            try:
                config.silence_threshold = float(threshold_input)
            except ValueError:
                console.print("[yellow]Invalid input, keeping current setting[/yellow]")
        
        # Save configuration
        config.save(config_path)
        console.print(f"\n[green]✓ Configuration saved to {config_path}[/green]")
        console.print(f"[green]✓ Language: {config.language}[/green]")
        console.print(f"[green]✓ Selected model: {model_input}[/green]")
        console.print(f"[green]✓ Silence duration: {config.silence_duration}s[/green]")
        console.print(f"[green]✓ Silence threshold: {config.silence_threshold}[/green]")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Configuration cancelled[/red]")
        sys.exit(1)
    
    # Flush all output streams
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Ensure clean exit
    sys.exit(0)


if __name__ == "__main__":
    # Run configuration if executed directly
    configure_voice()