import streamlit as st
import base64
import tempfile
from gtts import gTTS
import speech_recognition as sr
from translator_utils import stream_translation, detect_language

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Translator.AI 🌐",
    page_icon="🈶",
    layout="centered"
)

# --- UI & STYLES ---
st.markdown("<h1 style='text-align:center;'>🈶 Translator.AI - Powered by Groq</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Translate text and speech with real-time streaming using LLaMA3. 🌍</p>",
            unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "history" not in st.session_state:
    st.session_state.history = []
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "input_language" not in st.session_state:
    st.session_state.input_language = "Auto-Detect"
if "output_language" not in st.session_state:
    st.session_state.output_language = "Hindi"
if "last_translation_output" not in st.session_state:
    st.session_state.last_translation_output = None

# --- LANGUAGE DATA ---
# Dictionary for language selection and mapping to gTTS language codes
LANGUAGES = {
    "English": "en", "French": "fr", "German": "de", "Latin": "la",
    "Spanish": "es", "Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Marathi": "mr"
}
# Add "Auto-Detect" for the input dropdown
input_language_names = ["Auto-Detect"] + list(LANGUAGES.keys())
output_language_names = list(LANGUAGES.keys())

# --- UI COMPONENTS ---
st.markdown("---")

# Language Selection Row
col1, col_swap, col2 = st.columns([0.45, 0.1, 0.45])

with col1:
    st.session_state.input_language = st.selectbox(
        "🌐 From", input_language_names, key="input_lang_select",
        index=input_language_names.index(st.session_state.input_language)
    )

with col_swap:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacer for alignment
    if st.button("🔄", help="Swap Languages"):
        if st.session_state.input_language != "Auto-Detect":
            temp_lang = st.session_state.input_language
            st.session_state.input_language = st.session_state.output_language
            st.session_state.output_language = temp_lang
            st.rerun()

with col2:
    output_languages_list = [lang for lang in output_language_names if lang != st.session_state.input_language]
    st.session_state.output_language = st.selectbox(
        "🈯 To", output_languages_list, key="output_lang_select",
        index=output_languages_list.index(
            st.session_state.output_language) if st.session_state.output_language in output_languages_list else 0
    )

# Text Input
st.session_state.input_text = st.text_area(
    "✍️ Enter or Speak Text Below",
    value=st.session_state.input_text,
    placeholder="Type here or use the mic 🎤",
    height=120
)

# --- BUTTONS ---
col1_btn, col2_btn = st.columns(2)

# Speech-to-Text Button
with col1_btn:
    if st.button("🎙️ Use Microphone", use_container_width=True):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... Speak clearly.")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                st.session_state.input_text = recognizer.recognize_google(audio)
                st.success("Speech recognized! Click 'Translate'.")
                st.rerun()
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                st.error("❌ Could not understand audio or timed out. Please try again.")
            except sr.RequestError as e:
                st.error(f"❌ Speech service error: {e}")

# Translate Button
with col2_btn:
    if st.button("🔁 Translate", type="primary", use_container_width=True):
        if not st.session_state.input_text.strip():
            st.warning("⚠️ Please enter or speak some text to translate.")
        else:
            # Clear previous translation before starting a new one
            st.session_state.last_translation_output = None

            input_lang_for_translation = st.session_state.input_language

            # --- Auto-Detection Logic ---
            if input_lang_for_translation == "Auto-Detect":
                with st.spinner("Detecting language..."):
                    detected_lang = detect_language(st.session_state.input_text)
                if "failed" in detected_lang or detected_lang not in LANGUAGES:
                    st.error(
                        f"Could not reliably detect the language. Please select it manually. (Detected: {detected_lang})")
                    st.stop()
                st.info(f"Detected Language: **{detected_lang}**")
                input_lang_for_translation = detected_lang

            # --- Streaming Translation ---
            with st.container(border=True):
                st.markdown(f"**From ({input_lang_for_translation}):**\n> {st.session_state.input_text}")
                st.markdown("---")
                st.markdown(f"**To ({st.session_state.output_language}):**")

                with st.spinner("Translating..."):
                    # Use st.write_stream to render the streaming output
                    stream = stream_translation(
                        input_lang_for_translation,
                        st.session_state.output_language,
                        st.session_state.input_text
                    )
                    # This displays the stream and captures the full response
                    translated_text = st.write_stream(stream)

                # Store full translation for audio and download
                st.session_state.last_translation_output = translated_text

                # Add to history
                history_item = {
                    "input": st.session_state.input_text,
                    "output": translated_text,
                    "input_lang": input_lang_for_translation,
                    "output_lang": st.session_state.output_language
                }
                st.session_state.history.append(history_item)

# --- POST-TRANSLATION OUTPUTS (AUDIO & DOWNLOAD) ---
if st.session_state.last_translation_output:
    with st.container(border=True):
        st.subheader("Actions")
        col_audio, col_download = st.columns(2)

        # Text-to-Speech
        with col_audio:
            try:
                output_lang_code = LANGUAGES[st.session_state.output_language]
                tts = gTTS(st.session_state.last_translation_output, lang=output_lang_code)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tts.save(tmp_file.name)
                    st.audio(tmp_file.name, format="audio/mp3")
            except Exception as e:
                st.error(f"Could not generate audio: {e}")

        # Download Button
        with col_download:
            b64 = base64.b64encode(st.session_state.last_translation_output.encode()).decode()
            st.download_button(
                label="📄 Download as .txt",
                data=st.session_state.last_translation_output,
                file_name="translated_text.txt",
                mime="text/plain",
                use_container_width=True
            )

# --- CHAT HISTORY & CLEAR BUTTON ---
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 💬 Translation History")

    if st.button("🧹 Clear History"):
        st.session_state.history.clear()
        st.session_state.last_translation_output = None
        st.rerun()

    # Display last 5 translations using st.chat_message
    for item in reversed(st.session_state.history[-5:]):
        with st.chat_message("user"):
            st.write(f"**({item['input_lang']})** {item['input']}")
        with st.chat_message("assistant"):
            st.write(f"**({item['output_lang']})** {item['output']}")