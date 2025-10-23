import streamlit as st
import os
import json
import datetime
from vosk import Model, KaldiRecognizer
import wave
from rapidfuzz import fuzz

# ---- CONFIG ----
MODEL_PATH = "model"
WAKE_PHRASE = "hey assistant"
WAKE_THRESHOLD = 80

st.set_page_config(page_title="Offline Voice Assistant Demo", layout="wide")
st.title("🎙️ Offline AI Voice Assistant — Cloud Demo Version")
st.caption("👉 NOTE: Running in cloud mode (No direct microphone access).")

# ---- Load model if available ----
model_available = os.path.exists(MODEL_PATH)
if model_available:
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)

# ---- Intent/NLP ----
def match_intent(command):
    cmd = command.lower()
    if "time" in cmd:
        return "time"
    if "date" in cmd:
        return "date"
    if "hello" in cmd or "hi" in cmd:
        return "greet"
    if "calculator" in cmd:
        return "calculator"
    if "play music" in cmd:
        return "music"
    if "stop" in cmd:
        return "stop"
    return "unknown"

def perform_action(intent):
    if intent == "time":
        return f"It is {datetime.datetime.now().strftime('%I:%M %p')}"
    if intent == "date":
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}"
    if intent == "greet":
        return "Hello! How can I help you?"
    if intent == "calculator":
        return "Calculator mode enabled."
    if intent == "music":
        return "Playing music (demo only)."
    if intent == "stop":
        return "Goodbye!"
    return "Sorry, I didn't understand that."

# ---- UI ----
tab_input, tab_logs = st.tabs(["Input Commands", "Logs"])

if "logs" not in st.session_state:
    st.session_state.logs = []

with tab_input:
    st.subheader("Type a command")
    text_cmd = st.text_input("Write something like 'What is the time?'")

    if st.button("Process Command"):
        intent = match_intent(text_cmd)
        response = perform_action(intent)

        st.session_state.logs.append(("User", text_cmd))
        st.session_state.logs.append(("Assistant", response))

        st.success(f"Assistant: {response}")

    st.write("---")
    st.subheader("Or upload a voice file (Offline STT example)")
    audio = st.file_uploader("Upload WAV file (16khz Mono)", type=["wav"])

    if audio and model_available:
        wf = wave.open(audio, "rb")
        recognizer = KaldiRecognizer(model, wf.getframerate())

        text_result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text_result = result.get("text", "")

        st.write("Recognized Speech:", text_result)

        intent = match_intent(text_result)
        response = perform_action(intent)

        st.session_state.logs.append(("User(Audio)", text_result))
        st.session_state.logs.append(("Assistant", response))

        st.success(f"Assistant: {response}")
    elif audio and not model_available:
        st.warning("Model not uploaded to cloud — only UI demo active.")

with tab_logs:
    st.subheader("Interaction History")
    if st.session_state.logs:
        for sender, msg in st.session_state.logs[-50:]:
            st.write(f"**{sender}:** {msg}")
    else:
        st.info("No logs yet.")

st.markdown("---")
st.caption("Cloud demo version. Full offline microphone version runs locally.")
