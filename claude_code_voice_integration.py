#!/usr/bin/env python3
"""
Claude Code Interactive Mode with Voice Input
Simple wrapper that starts voice input alongside Claude Code
"""

import sys
import subprocess
from pathlib import Path

import pyperclip

# Import the voice module
from claude_code_voice_module import VoiceInput, VoiceConfig, configure_voice


def main():
    """Main entry point - very simple approach"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Code with Voice Input",
        add_help=False  # We'll pass --help to Claude itself
    )
    
    # Parse known args to separate our args from Claude's args
    parser.add_argument("--configure-voice", action="store_true",
                       help="Configure voice settings")
    
    # Parse only our arguments, rest go to Claude
    our_args, claude_args = parser.parse_known_args()
    
    if our_args.configure_voice:
        configure_voice()
        return 0
    
    # Show instructions
    print("Claude Code with Voice Support")
    print("=" * 40)
    
    voice_enabled = False
    voice_input = None
    
    # Try to start voice input by default
    try:
        voice_config_path = Path.home() / ".claude" / "voice_config.json"
        voice_input = VoiceInput(voice_config_path)
        voice_input.integration_mode = True
        
        # Set up voice callback with clipboard functionality
        def handle_voice_text(text: str):
            print(f"\n🎤 Voice transcribed: {text}")
            
            try:
                pyperclip.copy(text)
                print("📋 Copied to clipboard! Just paste into Claude (Cmd+V)")
            except Exception as e:
                print(f"❌ Could not copy to clipboard: {e}")
                print("💡 Copy and paste manually into Claude")
            
            print("-" * 50)
        
        voice_input.on_text = handle_voice_text
        voice_input.start(voice_input.on_text)
        voice_enabled = True
        
        print(f"🎙️ Voice input enabled! Press {voice_input.config.push_to_talk_key} to speak")
        
    except Exception as e:
        print(f"Could not start voice input: {e}")
        print("Continuing without voice support...")
    
    print("Starting Claude Code...")
    print("=" * 40)
    print()
    
    try:
        # Build the command and run Claude normally
        cmd = ['claude'] + claude_args
        result = subprocess.run(cmd)
        return_code = result.returncode
        
    except KeyboardInterrupt:
        return_code = 0
    except Exception as e:
        print(f"Error running Claude: {e}")
        return_code = 1
    finally:
        # Clean up voice input
        if voice_enabled and voice_input:
            try:
                voice_input.stop()
                print("\n🔇 Voice input stopped.")
            except:
                pass
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())