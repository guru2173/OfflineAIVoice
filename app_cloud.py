# app_cloud.py
import streamlit as st
import os
import json
import datetime
import wave
from vosk import Model, KaldiRecognizer
from rapidfuzz import fuzz

# ---- CONFIG ----
MODEL_PATH = "model"            # Optional on cloud; if absent app still works as UI demo
WAKE_PHRASE = "hey assistant"
WAKE_THRESHOLD = 75

st.set_page_config(page_title="Offline Voice Assistant Demo", layout="wide")
st.title("🎙️ Offline AI Voice Assistant — Cloud Demo Version")
st.caption("NOTE: Running in cloud/demo mode (no direct mic access). Upload WAV or type commands.")

# ---- Load model if available ----
model_available = os.path.exists(MODEL_PATH)
model = None
if model_available:
    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        st.warning(f"Vosk model found but failed to load: {e}")
        model_available = False

# ---- Intent/NLP (improved) ----
def normalize_text(t: str) -> str:
    if not t:
        return ""
    # simple normalization: lower, strip punctuation except math symbols
    import re
    t = t.lower().strip()
    t = re.sub(r"[^a-z0-9\s\+\-\*\/\.]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t

# Predefined intent phrases for fuzzy matching
INTENT_PHRASES = {
    "greet": ["hello", "hi", "hey", "hey there", "good morning", "good evening"],
    "how_are_you": ["how are you", "how r you", "how ru", "how's it going", "how are things"],
    "time": ["what time is it", "time", "current time", "tell me the time"],
    "date": ["what is the date", "today's date", "date"],
    "calculator": ["calculate", "what is", "compute", "evaluate", "plus", "minus", "times", "divided"],
    "music": ["play music", "play song", "music", "play some music"],
    "stop": ["stop", "exit", "quit", "goodbye", "bye"],
    "unknown": [""]  # fallback
}

def match_intent(command: str):
    """
    Return (intent, cleaned_command_or_param).
    Uses exact keywords first, then fuzzy matching against INTENT_PHRASES.
    """
    cmd_raw = command or ""
    cmd = normalize_text(cmd_raw)

    if not cmd:
        return ("unknown", None)

    # Quick exact checks
    if any(word in cmd for word in ["how are you", "how r you", "how are u"]):
        return ("how_are_you", None)
    if any(word in cmd for word in ["hello", "hi", "hey"]):
        return ("greet", None)
    if "time" in cmd and len(cmd) < 40:
        return ("time", None)
    if "date" in cmd:
        return ("date", None)
    if any(x in cmd for x in ["play music", "play song", "music"]):
        return ("music", None)
    if "calculator" in cmd or "calculate" in cmd or any(op in cmd for op in ["plus", "minus", "times", "divided", "over"]):
        return ("calculator", cmd)

    # Fuzzy match - pick best intent if score is reasonably high
    best_intent = "unknown"
    best_score = 0
    for intent, phrases in INTENT_PHRASES.items():
        for phr in phrases:
            score = fuzz.partial_ratio(phr, cmd)  # 0..100
            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 70:
        return (best_intent, cmd)
    # fallback: unknown
    return ("unknown", cmd)

def perform_action(intent, param=None):
    if intent == "how_are_you":
        return "I'm an offline assistant — running great! How can I help you?"
    if intent == "greet":
        return "Hello! How can I help you?"
    if intent == "time":
        return f"It is {datetime.datetime.now().strftime('%I:%M %p')}"
    if intent == "date":
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}"
    if intent == "music":
        return "Playing music (demo)."
    if intent == "stop":
        return "Goodbye!"
    if intent == "calculator":
        # Try to parse simple expression from param
        if not param:
            return "Calculator mode: say something like 'calculate 5 plus 3' or type an expression."
        # replace words to symbols
        expr = param
        expr = expr.replace("multiplied by", "*")
        expr = expr.replace("times", "*")
        expr = expr.replace("plus", "+")
        expr = expr.replace("minus", "-")
        expr = expr.replace("divided by", "/")
        expr = expr.replace("over", "/")
        # keep numbers and operators
        allowed = "0123456789+-*/.() "
        cleaned = "".join([c for c in expr if c in allowed])
        try:
            result = eval(cleaned, {"__builtins__":{}})
            return f"The result is {result}"
        except Exception:
            return "Sorry, I couldn't parse that expression. Try a simpler expression like '12 + 5'."
    return "Sorry, I didn't understand that. (Try: 'What time is it?' or 'How are you?')"

# ---- UI ----
tab_input, tab_logs = st.tabs(["Input Commands", "Upload Audio (optional)"])
if "logs" not in st.session_state:
    st.session_state.logs = []

with tab_input:
    st.subheader("Type a command (recommended for Streamlit Cloud demo)")
    text_cmd = st.text_input("Try small talk like: 'How are you' or commands like 'What time is it?'")

    if st.button("Process Command"):
        if not text_cmd.strip():
            st.warning("Please type a command or upload audio.")
        else:
            intent, param = match_intent(text_cmd)
            response = perform_action(intent, param)
            st.session_state.logs.append(("User", text_cmd))
            st.session_state.logs.append(("Assistant", response))
            st.success(f"Assistant: {response}")

with tab_logs:
    st.subheader("Upload WAV to run offline STT on server (if model present)")
    audio = st.file_uploader("Upload WAV (16 kHz mono recommended)", type=["wav"])
    if audio:
        if not model_available:
            st.warning("Vosk model not present on server. Upload model to use STT here, or use text input.")
        else:
            try:
                wf = wave.open(audio, "rb")
                sr = wf.getframerate()
                rec = KaldiRecognizer(model, sr)
                rec.SetWords(True)
                text_result = ""
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        part = json.loads(rec.Result())
                        text_result += " " + part.get("text", "")
                # final partial/final
                final = json.loads(rec.FinalResult())
                text_result += " " + final.get("text", "")
                text_result = text_result.strip()
                if not text_result:
                    st.info("No speech recognized in the file.")
                else:
                    st.write("Recognized Speech:", text_result)
                    intent, param = match_intent(text_result)
                    response = perform_action(intent, param)
                    st.session_state.logs.append(("User(Audio)", text_result))
                    st.session_state.logs.append(("Assistant", response))
                    st.success(f"Assistant: {response}")
            except Exception as e:
                st.error(f"Failed to process audio file: {e}")

# ---- Interaction history ----
st.markdown("---")
st.subheader("Interaction History (latest 50)")
logs_to_show = st.session_state.logs[-50:]
if not logs_to_show:
    st.info("No interactions yet. Type a command or upload a WAV file.")
else:
    for who, msg in logs_to_show:
        if who.startswith("User"):
            st.write(f"**{who}:** {msg}")
        else:
            st.write(f"**{who}:** {msg}")

st.markdown("---")
st.caption("Cloud demo version. To run the full offline assistant with microphone and TTS, run the local version (app.py) with Vosk + sound device and eSpeak installed.")
