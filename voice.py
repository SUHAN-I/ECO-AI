# ============================================================
# FILE: voice.py
# PURPOSE: Voice input (Whisper STT) + Voice output (gTTS)
# INSTALL: pip install openai-whisper gtts soundfile numpy
# ============================================================

import io
import os
import tempfile
import numpy as np

# ── CONFIGURATION ────────────────────────────────────────────
WHISPER_MODEL_SIZE = "tiny"   # tiny = fastest, lightest for Streamlit Cloud


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Load Whisper Model (once at startup)
# ════════════════════════════════════════════════════════════
def load_whisper_model():
    """
    Loads Whisper tiny model for speech-to-text.
    Cache with @st.cache_resource in Streamlit.

    Returns:
        whisper model object or None if failed
    """
    try:
        import whisper
        print(f"⏳ Loading Whisper {WHISPER_MODEL_SIZE}...")
        model = whisper.load_model(WHISPER_MODEL_SIZE)
        print(f"✅ Whisper {WHISPER_MODEL_SIZE} loaded!")
        return model
    except Exception as e:
        print(f"❌ Whisper load failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Speech to Text (Whisper)
# ════════════════════════════════════════════════════════════
def speech_to_text(whisper_model, audio_bytes, language="en"):
    """
    Converts audio bytes to text using Whisper tiny.

    Args:
        whisper_model : loaded Whisper model
        audio_bytes   : raw audio bytes (from st.audio_input)
        language      : "en" for English, "ur" for Urdu

    Returns:
        transcribed text string or None if failed
    """
    if whisper_model is None:
        print("❌ Whisper model not loaded")
        return None

    try:
        print("🎤 Transcribing audio...")

        # Save bytes to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Transcribe
        lang_code = "ur" if language == "urdu" else "en"
        result    = whisper_model.transcribe(
            tmp_path,
            language       = lang_code,
            fp16           = False,   # CPU-safe
            condition_on_previous_text = False
        )

        text = result.get("text", "").strip()
        os.unlink(tmp_path)   # Clean up temp file

        if text:
            print(f"✅ Transcribed: '{text}'")
        else:
            print("⚠️ No speech detected")

        return text if text else None

    except Exception as e:
        print(f"❌ STT error: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Text to Speech (gTTS — primary)
# ════════════════════════════════════════════════════════════
def text_to_speech_gtts(text, language="english"):
    """
    Converts text to speech using gTTS (Google TTS).
    Free, lightweight, no API key needed.

    Args:
        text     : text to speak
        language : "english" or "urdu"

    Returns:
        audio bytes (MP3) or None if failed
    """
    try:
        from gtts import gTTS

        lang_code = "ur" if language == "urdu" else "en"
        tts       = gTTS(text=text, lang=lang_code, slow=False)

        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)

        audio_bytes = buf.read()
        print(f"✅ gTTS generated: {len(audio_bytes)} bytes")
        return audio_bytes

    except Exception as e:
        print(f"❌ gTTS error: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Text to Speech (streamlit-tts — fallback)
# ════════════════════════════════════════════════════════════
def text_to_speech_streamlit(text, language="english"):
    """
    Uses streamlit-tts browser-based TTS as fallback.
    No audio bytes returned — renders directly in Streamlit.

    Args:
        text     : text to speak
        language : "english" or "urdu"

    Returns:
        True if rendered, False if failed
    """
    try:
        from streamlit_tts import auto_play, text_to_audio

        lang_code = "ur-PK" if language == "urdu" else "en-US"
        auto_play(text, language=lang_code)
        print("✅ streamlit-tts rendered")
        return True

    except ImportError:
        print("⚠️ streamlit-tts not installed")
        return False
    except Exception as e:
        print(f"❌ streamlit-tts error: {e}")
        return False


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Main TTS (tries gTTS first, then fallback)
# ════════════════════════════════════════════════════════════
def speak(text, language="english", max_chars=500):
    """
    Main TTS function. Tries gTTS first, streamlit-tts as fallback.
    Truncates long text to keep audio short.

    Args:
        text      : text to speak
        language  : "english" or "urdu"
        max_chars : max characters to speak (keeps audio short)

    Returns:
        dict with:
            method    : "gtts" | "streamlit_tts" | "none"
            audio     : MP3 bytes (for gTTS) or None
            text_used : actual text spoken
    """
    # Truncate to first max_chars characters
    if len(text) > max_chars:
        # Find last sentence end before limit
        truncated = text[:max_chars]
        for sep in [".", "!", "?", "\n"]:
            idx = truncated.rfind(sep)
            if idx > max_chars // 2:
                truncated = truncated[:idx+1]
                break
        text = truncated

    print(f"\n🔊 Speaking ({language}): {text[:60]}...")

    # Try gTTS first (best quality + returns bytes)
    audio = text_to_speech_gtts(text, language)
    if audio:
        return {"method": "gtts", "audio": audio, "text_used": text}

    # Fallback to streamlit-tts (browser-based)
    success = text_to_speech_streamlit(text, language)
    if success:
        return {"method": "streamlit_tts", "audio": None, "text_used": text}

    return {"method": "none", "audio": None, "text_used": text}


# ════════════════════════════════════════════════════════════
# FUNCTION 6: Render Voice Result in Streamlit
# ════════════════════════════════════════════════════════════
def render_tts_in_streamlit(st, tts_result):
    """
    Renders TTS audio output in Streamlit UI.

    Args:
        st         : streamlit module
        tts_result : dict from speak()
    """
    if tts_result["method"] == "gtts" and tts_result["audio"]:
        st.audio(tts_result["audio"], format="audio/mp3", autoplay=True)
        st.caption("🔊 AI voice response (gTTS)")

    elif tts_result["method"] == "streamlit_tts":
        st.caption("🔊 AI voice response (browser TTS)")

    else:
        st.caption("⚠️ Voice output unavailable — check internet connection")


# ════════════════════════════════════════════════════════════
# FUNCTION 7: Render Voice Input in Streamlit
# ════════════════════════════════════════════════════════════
def render_voice_input(st, whisper_model, language="english"):
    """
    Renders voice input widget and returns transcribed text.

    Args:
        st            : streamlit module
        whisper_model : loaded Whisper model
        language      : "english" or "urdu"

    Returns:
        transcribed text string or None
    """
    lang_hint = "Speak in Urdu…" if language == "urdu" else "Speak in English…"

    st.markdown(f"""
    <div style="background:#f0f7f0;border-radius:12px;padding:1rem;
                border:2px dashed #2db52d;text-align:center;margin-bottom:1rem">
        <div style="font-size:1.5rem">🎤</div>
        <div style="font-size:0.85rem;color:#555">{lang_hint}</div>
    </div>
    """, unsafe_allow_html=True)

    audio = st.audio_input("Record your question", label_visibility="collapsed")

    if audio is not None:
        with st.spinner("🎤 Transcribing…"):
            text = speech_to_text(whisper_model, audio.getvalue(), language)

        if text:
            st.success(f"📝 You said: *{text}*")
            return text
        else:
            st.warning("⚠️ Could not transcribe. Please speak clearly and try again.")

    return None


# ════════════════════════════════════════════════════════════
# COLAB / STANDALONE TEST
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print("  VOICE MODULE — STANDALONE TEST")
    print("=" * 50)

    # Test Whisper load
    model = load_whisper_model()
    print(f"\nWhisper loaded: {model is not None}")

    # Test gTTS
    print("\nTesting gTTS...")
    result = speak("Hello! This is Eco AI Pakistan waste manager.", "english")
    print(f"TTS method: {result['method']}")
    if result["audio"]:
        with open("test_output.mp3", "wb") as f:
            f.write(result["audio"])
        print("✅ Audio saved to test_output.mp3")

    print("\n✅ Voice module test complete!")
