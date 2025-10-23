# app_cloud.py (CLOUD DEMO ONLY - NO STT)
import streamlit as st
import datetime
from rapidfuzz import fuzz

st.set_page_config(page_title="Offline AI Assistant - Demo", layout="wide")
st.title("🎙️ Offline AI Voice Assistant — Cloud Demo")
st.caption("Cloud version (Text-based test). Full voice features work offline.")

# ---- Intent/NLP ----
def normalize(t):
    import re
    t = t.lower().strip()
    t = re.sub(r"[^a-z0-9\s\+\-\*\/\.]", " ", t)
    return re.sub(r"\s+", " ", t)

INTENT_PHRASES = {
    "greet": ["hi", "hello", "hey"],
    "how_are_you": ["how are you", "how's it going"],
    "time": ["what time", "current time"],
    "date": ["what date", "today date"],
    "calculator": ["calculate", "what is", "plus", "minus", "times", "divided"],
    "stop": ["bye", "stop", "exit"],
}

def match_intent(cmd):
    c = normalize(cmd)
    if "how are" in c:
        return "how_are_you", None
    if any(w in c for w in ["hi","hello","hey"]):
        return "greet", None
    if "time" in c:
        return "time", None
    if "date" in c:
        return "date", None
    if any(op in c for op in ["plus","minus","times","divided","calculate"]):
        return "calculator", c

    # fuzzy fallback
    best, score = "unknown", 0
    for intent, phrases in INTENT_PHRASES.items():
        for phr in phrases:
            s = fuzz.partial_ratio(phr, c)
            if s > score:
                score, best = s, intent
    return (best if score > 70 else "unknown"), c

def perform(intent, param):
    if intent == "greet":
        return "Hello! How can I assist you?"
    if intent == "how_are_you":
        return "I'm running perfectly offline on your PC! 😄"
    if intent == "time":
        return datetime.datetime.now().strftime("Time: %I:%M %p")
    if intent == "date":
        return datetime.datetime.now().strftime("Date: %A, %B %d, %Y")
    if intent == "stop":
        return "Goodbye!"
    if intent == "calculator":
        expr = (param or "")
        expr = (expr.replace("plus","+")
                     .replace("minus","-")
                     .replace("times","*")
                     .replace("divided","/"))
        try:
            result = eval("".join(c for c in expr if c in "0123456789+-*/."))
            return f"Result: {result}"
        except:
            return "Calculator error. Try: 5 plus 3"
    return "Sorry, I didn’t understand. Try: 'how are you' or 'time'"

# ---- UI ----
if "log" not in st.session_state:
    st.session_state.log = []

cmd = st.text_input("Type a command here:")
if st.button("Send"):
    if cmd.strip():
        intent, param = match_intent(cmd)
        reply = perform(intent, param)
        st.session_state.log += [(f"You", cmd), ("Assistant", reply)]
        st.success(reply)
    else:
        st.warning("Please type something!")

st.markdown("### 📝 Interaction Log")
for who, msg in st.session_state.log[-40:]:
    st.write(f"**{who}:** {msg}")

st.markdown("---")
st.info("✅ Full Offline Version supports microphone & voice commands. "
        "Download & run locally for full functionality.")
