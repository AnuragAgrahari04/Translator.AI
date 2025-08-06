# # import os
# # import json
# # from langchain_groq import ChatGroq  # ✅ Correct import
# # from langchain_core.prompts import ChatPromptTemplate
# #
# # # Load GROQ API Key
# # working_dir = os.path.dirname(os.path.abspath(__file__))
# # config_data = json.load(open(f"{working_dir}/config.json"))
# # GROQ_API_KEY = config_data["GROQ_API_KEY"]
# #
# # # Initialize Groq LLM
# # llm = ChatGroq(model="llama3-70b-8192", api_key=GROQ_API_KEY)
# #
# # def translate(input_language, output_language, input_text):
# #     prompt = ChatPromptTemplate.from_messages(
# #         [
# #             ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
# #             ("human", "{inputs}")
# #         ]
# #     )
# #
# #     chain = prompt | llm
# #
# #     try:
# #         response = chain.invoke({
# #             "input_language": input_language,
# #             "output_language": output_language,
# #             "inputs": input_text
# #         })
# #         return response.content
# #     except Exception as e:
# #         return f"❌ Translation failed: {str(e)}"
# #

# import os
# import json
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate

# # --- API KEY & LLM INITIALIZATION ---
# try:
#     # Load GROQ API Key from config file
#     working_dir = os.path.dirname(os.path.abspath(__file__))
#     config_data = json.load(open(f"{working_dir}/config.json"))
#     GROQ_API_KEY = config_data["GROQ_API_KEY"]

#     # Initialize Groq LLM for translation and detection
#     llm = ChatGroq(model="llama3-70b-8192", api_key=GROQ_API_KEY)

# except (FileNotFoundError, KeyError) as e:
#     # Handle missing config file or key
#     GROQ_API_KEY = None
#     llm = None
#     print(f"Warning: Configuration error - {e}. Translator will not function.")


# # --- CORE FUNCTIONS ---

# def stream_translation(input_language, output_language, input_text):
#     """
#     Yields the translated text chunk by chunk.
#     """
#     if not llm:
#         yield "❌ LLM not initialized. Check your API key configuration."
#         return

#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
#             ("human", "{inputs}")
#         ]
#     )
#     chain = prompt | llm

#     try:
#         # Use .stream() which returns a generator for real-time output
#         for chunk in chain.stream({
#             "input_language": input_language,
#             "output_language": output_language,
#             "inputs": input_text
#         }):
#             yield chunk.content
#     except Exception as e:
#         yield f"❌ Translation failed: {str(e)}"

# def detect_language(text):
#     """
#     Detects the language of the given text.
#     """
#     if not llm:
#         return "Error: LLM not initialized."

#     detect_prompt = ChatPromptTemplate.from_messages([
#         ("system", "You are a language detection expert. Analyze the following text and respond with only the name of the language in English (e.g., 'French', 'Spanish', 'Hindi'). Do not add any other words or punctuation."),
#         ("human", "{text_to_detect}")
#     ])
#     chain = detect_prompt | llm

#     try:
#         response = chain.invoke({"text_to_detect": text})
#         # Clean up the response to get only the language name
#         return response.content.strip()
#     except Exception as e:

#         return f"Detection failed: {e}"


import streamlit as st
import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# --- API KEY & LLM INITIALIZATION ---

GROQ_API_KEY = None
llm = None

# This is the new, secure way to load the API key.
# It tries to load from Streamlit's secrets first (for deployment).
# If that fails, it falls back to the local config.json (for local development).
try:
    # For Streamlit Community Cloud
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except (KeyError, AttributeError):
    # For local development
    print("Streamlit secrets not found. Falling back to local config.json.")
    try:
        working_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(working_dir, "config.json")
        with open(config_path) as config_file:
            config_data = json.load(config_file)
            GROQ_API_KEY = config_data["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        print("Warning: config.json not found or key is missing.")
        # The app will show an error message in the UI
        pass

# Initialize the LLM only if the API key was found
if GROQ_API_KEY:
    llm = ChatGroq(model="llama3-70b-8192", api_key=GROQ_API_KEY)


# --- CORE FUNCTIONS ---

def stream_translation(input_language, output_language, input_text):
    """
    Yields the translated text chunk by chunk.
    """
    if not llm:
        yield "❌ LLM not initialized. Check your API key configuration in Streamlit Secrets."
        return

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
            ("human", "{inputs}")
        ]
    )
    chain = prompt | llm
    try:
        for chunk in chain.stream({
            "input_language": input_language,
            "output_language": output_language,
            "inputs": input_text
        }):
            yield chunk.content
    except Exception as e:
        yield f"❌ Translation failed: {str(e)}"

def detect_language(text):
    """
    Detects the language of the given text.
    """
    if not llm:
        return "Error: LLM not initialized."

    detect_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a language detection expert. Respond with only the language name."),
        ("human", "{text_to_detect}")
    ])
    chain = detect_prompt | llm
    try:
        response = chain.invoke({"text_to_detect": text})
        return response.content.strip()
    except Exception as e:
        return f"Detection failed: {e}"
