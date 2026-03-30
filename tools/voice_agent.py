#!/usr/bin/env python3
"""
Jarvis — Voice agent for Matt Anthony Photography.

Press Enter to talk. Speaks back through your speakers.
Connects to all business systems via Claude API tool_use.

Usage:
    python3 tools/voice_agent.py

Requires in .env:
    ANTHROPIC_API_KEY
    OPENAI_API_KEY
"""

import os
import sys
import io
import json
import time
import wave
import struct
import select
import termios
import tty
from queue import Queue, Empty
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
import anthropic
import openai
import webrtcvad

from dotenv import load_dotenv

# Add tools dir to path
sys.path.insert(0, os.path.dirname(__file__))
from voice_tools import TOOLS, execute_tool

# ─── Config ───────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CONVERSATION_TIMEOUT = 30       # seconds before requiring Enter again
MAX_RECORDING_SECONDS = 30      # max single utterance length
SILENCE_THRESHOLD_FRAMES = 40   # ~1.2s of silence = end of speech (at 30ms/frame)
VAD_AGGRESSIVENESS = 2          # 0-3, higher = more aggressive filtering
MAX_HISTORY = 20                # rolling conversation window
SAMPLE_RATE = 16000             # Whisper sample rate
TTS_SAMPLE_RATE = 24000         # OpenAI TTS output rate
TTS_VOICE = "echo"              # alloy, echo, fable, onyx, nova, shimmer
RECORD_BLOCK_SIZE = 480         # 30ms at 16kHz for VAD

SYSTEM_PROMPT = """You are Jarvis, the voice assistant for Matt Anthony Photography.

Matt is an architectural and interior photographer based in Squamish, BC. You manage his entire business operations through voice: sales pipeline, email, finances, marketing campaigns, content calendar, scheduling, and production.

VOICE RESPONSE RULES:
- Be concise. This is spoken, not written. 2-3 sentences unless Matt asks for detail.
- No bullet points, no markdown, no special characters.
- Round numbers for speech: say "about twelve thousand" not "$12,347.82".
- When listing items, limit to top 3-5 unless asked for more.
- Use natural spoken language. Say "you've got" not "there are".
- For times, say "two PM" not "14:00".
- If a tool returns a lot of data, summarize the key points.
- If something fails, say so plainly and suggest an alternative.

Current date: {today}
Timezone: America/Vancouver (Pacific Time)
"""


# ─── Keyboard Input ───────────────────────────────────────────────────────

def key_pressed():
    """Check if a key was pressed (non-blocking). Returns True if Enter/any key hit."""
    if select.select([sys.stdin], [], [], 0.0)[0]:
        sys.stdin.read(1)
        return True
    return False


# ─── Audio Feedback (programmatic chimes) ─────────────────────────────────

def play_chime(chime_type):
    """Play a short audio chime for state transitions."""
    sr = TTS_SAMPLE_RATE
    try:
        if chime_type == "wake":
            t1 = np.linspace(0, 0.08, int(sr * 0.08), endpoint=False)
            t2 = np.linspace(0, 0.08, int(sr * 0.08), endpoint=False)
            tone = np.concatenate([
                np.sin(2 * np.pi * 580 * t1) * 0.25,
                np.sin(2 * np.pi * 880 * t2) * 0.25,
            ])
        elif chime_type == "thinking":
            t = np.linspace(0, 0.04, int(sr * 0.04), endpoint=False)
            tone = np.sin(2 * np.pi * 660 * t) * 0.12
        elif chime_type == "sleep":
            t = np.linspace(0, 0.12, int(sr * 0.12), endpoint=False)
            fade = np.linspace(0.2, 0, len(t))
            tone = np.sin(2 * np.pi * 580 * t) * fade
        elif chime_type == "error":
            t = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
            tone = np.concatenate([
                np.sin(2 * np.pi * 300 * t) * 0.2,
                np.sin(2 * np.pi * 220 * t) * 0.2,
            ])
        else:
            return

        sd.play(tone.astype(np.float32), samplerate=sr)
        sd.wait()
    except Exception:
        pass


# ─── Microphone Recording ────────────────────────────────────────────────

def record_audio():
    """Record from mic until speech ends. Returns raw PCM bytes or None."""
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    audio_queue = Queue()
    vad_frame_samples = int(SAMPLE_RATE * 0.03)  # 480 samples = 30ms

    def callback(indata, frames, time_info, status):
        pcm_int16 = (indata[:, 0] * 32768).astype(np.int16)
        audio_queue.put(pcm_int16.copy())

    all_frames = []
    speech_started = False
    silence_frames = 0
    start_time = time.time()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=vad_frame_samples,
        callback=callback,
    )

    with stream:
        while time.time() - start_time < MAX_RECORDING_SECONDS:
            try:
                frame = audio_queue.get(timeout=0.1)
            except Empty:
                continue

            all_frames.append(frame)

            if len(frame) < vad_frame_samples:
                continue

            chunk_bytes = struct.pack(f"{vad_frame_samples}h", *frame[:vad_frame_samples])
            try:
                is_speech = vad.is_speech(chunk_bytes, SAMPLE_RATE)
            except Exception:
                continue

            if is_speech:
                speech_started = True
                silence_frames = 0
            elif speech_started:
                silence_frames += 1
                if silence_frames >= SILENCE_THRESHOLD_FRAMES:
                    break

    if not speech_started or len(all_frames) < 10:
        return None

    all_samples = np.concatenate(all_frames)

    if len(all_samples) < SAMPLE_RATE * 0.3:
        return None

    return all_samples.tobytes()


# ─── Speech-to-Text ──────────────────────────────────────────────────────

def transcribe(client, audio_bytes):
    """Transcribe raw PCM audio bytes using OpenAI Whisper."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)
    buf.seek(0)
    buf.name = "audio.wav"

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
        language="en",
    )
    return result.text.strip()


# ─── Text-to-Speech ──────────────────────────────────────────────────────

def speak(client, text):
    """Convert text to speech and play it."""
    if not text or not text.strip():
        return

    if len(text) > 600:
        text = text[:600] + "... I can give you more detail if you'd like."

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=TTS_VOICE,
            input=text,
            response_format="pcm",
        )
        audio_data = np.frombuffer(response.content, dtype=np.int16)
        audio_float = audio_data.astype(np.float32) / 32768.0
        sd.play(audio_float, samplerate=TTS_SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print(f"[Jarvis] TTS error: {e}")


# ─── Claude API (Brain) ──────────────────────────────────────────────────

def call_claude(client, conversation_history):
    """Call Claude API with tool definitions and conversation history."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    return client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT.format(today=today),
        tools=TOOLS,
        messages=conversation_history,
    )


def process_response(client, conversation_history, response):
    """Handle Claude's response, executing tools as needed in a loop."""
    while response.stop_reason == "tool_use":
        conversation_history.append({
            "role": "assistant",
            "content": response.content,
        })

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[Jarvis] Running tool: {block.name}")
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)[:4000],
                })

        conversation_history.append({
            "role": "user",
            "content": tool_results,
        })

        response = call_claude(client, conversation_history)

    text_parts = []
    for block in response.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)

    final_text = " ".join(text_parts)

    conversation_history.append({
        "role": "assistant",
        "content": response.content,
    })

    return final_text


# ─── Main Loop ────────────────────────────────────────────────────────────

def validate_env():
    """Check all required environment variables are set."""
    required = {
        "ANTHROPIC_API_KEY": "Get from console.anthropic.com",
        "OPENAI_API_KEY": "Get from platform.openai.com/api-keys",
    }
    missing = []
    for key, hint in required.items():
        if not os.getenv(key):
            missing.append(f"  {key} — {hint}")
    if missing:
        print("[Jarvis] Missing environment variables in .env:")
        print("\n".join(missing))
        sys.exit(1)


def main():
    validate_env()

    claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("[Jarvis] Voice agent ready.")
    print("[Jarvis] Press ENTER to talk. Press Ctrl+C to quit.")
    print("[Jarvis] After a response, just press ENTER again for follow-ups (30s window).\n")

    # Set terminal to raw mode for non-blocking key detection
    old_settings = termios.tcgetattr(sys.stdin)

    conversation_history = []
    last_response_time = None
    in_conversation = False

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:
            # Show appropriate prompt
            if not in_conversation:
                # Reset to normal mode briefly to show prompt
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                print("[Jarvis] Press ENTER to talk...", end="", flush=True)
                tty.setcbreak(sys.stdin.fileno())

            # Wait for keypress (or timeout in conversation mode)
            while True:
                if in_conversation:
                    elapsed = time.time() - last_response_time
                    if elapsed > CONVERSATION_TIMEOUT:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        print("\n[Jarvis] Conversation ended. Press ENTER to start fresh.\n")
                        tty.setcbreak(sys.stdin.fileno())
                        play_chime("sleep")
                        in_conversation = False
                        conversation_history = []
                        break

                # Non-blocking check for keypress
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)
                    if ch in ("\n", "\r", " "):
                        # Activate!
                        break
                    elif ch == "\x03":  # Ctrl+C
                        raise KeyboardInterrupt

            # If we broke out due to timeout, loop back
            if not in_conversation and last_response_time is not None:
                last_response_time = None
                continue

            # ── Record ──
            # Restore terminal for clean output
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            play_chime("wake")
            print("\n[Jarvis] Listening... (speak now, pause when done)")

            audio_data = record_audio()

            if not audio_data:
                print("[Jarvis] No speech detected.")
                tty.setcbreak(sys.stdin.fileno())
                if in_conversation:
                    continue
                else:
                    continue

            # ── Transcribe ──
            print("[Jarvis] Transcribing...")
            play_chime("thinking")
            try:
                transcript = transcribe(openai_client, audio_data)
            except Exception as e:
                print(f"[Jarvis] Transcription error: {e}")
                play_chime("error")
                speak(openai_client, "Sorry, I couldn't hear that clearly. Try again.")
                tty.setcbreak(sys.stdin.fileno())
                continue

            if not transcript:
                print("[Jarvis] Empty transcript.")
                tty.setcbreak(sys.stdin.fileno())
                continue

            print(f"\n[You] {transcript}")

            # ── Add to conversation ──
            if not in_conversation:
                conversation_history = []

            conversation_history.append({
                "role": "user",
                "content": transcript,
            })

            if len(conversation_history) > MAX_HISTORY:
                conversation_history = conversation_history[-MAX_HISTORY:]

            # ── Think ──
            print("[Jarvis] Thinking...")
            try:
                response = call_claude(claude_client, conversation_history)
                final_text = process_response(
                    claude_client, conversation_history, response
                )
            except Exception as e:
                print(f"[Jarvis] Error: {e}")
                play_chime("error")
                speak(openai_client, "Sorry, I had trouble processing that. Try again.")
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()
                tty.setcbreak(sys.stdin.fileno())
                continue

            print(f"\n[Jarvis] {final_text}\n")

            # ── Speak ──
            speak(openai_client, final_text)

            last_response_time = time.time()
            in_conversation = True

            # Back to raw mode for key detection
            tty.setcbreak(sys.stdin.fileno())
            print("[Jarvis] Press ENTER for follow-up...", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\n[Jarvis] Shutting down. Goodbye!")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    main()
