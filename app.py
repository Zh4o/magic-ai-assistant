import streamlit as st
from google import genai
from google.genai import types
import gspread
import json
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Sam, your Loyalist Concierge",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Authentication & Configuration ---
# The new Client() automatically looks for the GEMINI_API_KEY environment variable.
# We will set it from Streamlit secrets for deployment.
try:
    os.environ['GEMINI_API_KEY'] = st.secrets["gemini"]["GEMINI_API_KEY"]
    client = genai.Client()
except Exception:
    st.error("Gemini API key not found. Please add it to your Streamlit secrets as GEMINI_API_KEY.")
    st.stop()

# Configure Google Sheets API
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    spreadsheet = gc.open_by_key(st.secrets["google_sheet"]["GOOGLE_SHEET_KEY"]) # Use sheet key for robustness
    worksheet = spreadsheet.worksheet("Sheet1")
except Exception as e:
    st.error(f"Google Sheets credentials or Sheet Key not found. Please check your secrets. Error: {e}")
    st.stop()

# --- Core App Components ---

SAM_INSTRUCTIONS = """
You are Sam, an expert concierge for planning team dinners. Your tone is friendly, professional, and enthusiastic. 
Your primary goals are to naturally gather these 7 details:
- Party Size
- Occasion
- Vibe (e.g., casual, fancy, lively)
- Budget per person
- Date
- Special requests or dietary restrictions
- A contact email to send the options to.

Today's date is October 30, 2025.

Keep your responses concise and focused on gathering the next piece of information. Do not suggest restaurants.
Once you have collected ALL details, with the Contact Email being the last critical piece, do two things in your final response:
1. Confirm you have everything you need and that you'll be in touch at their email.
2. Tell the user to hit the 'Finalize Details' button below to save the information.
3. IMPORTANT: Append the special token `[READY_TO_FINALIZE]` at the very end of that specific message. You must not say this token out loud or mention it to the user.
"""

SUGGESTIONS = {
    "🎉 Sales Team Celebration": "Planning a dinner for our sales team to celebrate a great quarter. Maybe 15 people.",
    "🤝 Client Dinner in SoHo": "I need to plan an impressive dinner for clients in SoHo.",
    "🚀 Casual Team Lunch": "Can you help me find a spot for a casual team lunch for 10?",
}

def clear_conversation():
    """Resets the chat history and all state flags."""
    st.session_state.messages = []
    if "suggestion_processed" in st.session_state:
        st.session_state.suggestion_processed = False
    # Add this line to reset the finalize state
    if "ready_to_finalize" in st.session_state:
        st.session_state.ready_to_finalize = False

# --- UI Rendering ---
title_col, restart_col = st.columns([5, 1])
with title_col:
    st.title("Sam, your Concierge")
with restart_col:
    if "messages" in st.session_state and st.session_state.messages:
        st.button("Restart", on_click=clear_conversation, use_container_width=True)

# --- Main Chat Interface ---

# Initialize session state keys if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestion_processed" not in st.session_state:
    st.session_state.suggestion_processed = False

# Display the initial welcome screen with suggestions ONLY if the chat is new.
if not st.session_state.messages:
    # Display the pills. The user's selection is automatically stored in the key.
    selected_suggestion = st.pills(
        label="Or, start with an example:",
        options=list(SUGGESTIONS.keys()),
        key="selected_suggestion_pills",
    )

    # If a pill is selected AND we haven't processed it yet...
    if selected_suggestion and not st.session_state.suggestion_processed:
        # Get the full prompt from the dictionary.
        user_message = SUGGESTIONS[selected_suggestion]
        # Add the message to the chat history.
        st.session_state.messages.append({"role": "user", "content": user_message})
        # Set our flag to True so this block doesn't run again.
        st.session_state.suggestion_processed = True
        # Immediately rerun the script to display the message and trigger the AI response.
        st.rerun()

# Display the entire chat history on each script run
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle Gemini API Call ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Construct the conversation history for the API
    conversation_history = [
        {"role": "model" if m["role"] == "assistant" else m["role"], "parts": [{"text": m["content"]}]}
        for m in st.session_state.messages
    ]

    # Call the Gemini API
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conversation_history,
        config=types.GenerateContentConfig(
        system_instruction=SAM_INSTRUCTIONS)
    )
    response_text = response.text

    # Check for the special token
    if "[READY_TO_FINALIZE]" in response_text:
        st.session_state.ready_to_finalize = True
        response_text = response_text.replace("[READY_TO_FINALIZE]", "").strip()

    # Append the new response to the messages list
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Rerun the script so the display loop can show the new message
    st.rerun()

# --- Persistent Chat Input ---
# This will now appear at the bottom, after the initial suggestions are handled.
if prompt := st.chat_input("What can I help you plan?"):
    # Append the user's new message to the chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Rerun the script to display the new message and trigger the assistant's response
    st.rerun()


# --- Backend Skill: The "Finalize" Button ---

# Only show the button if the AI has signaled that all required information is collected.
if st.session_state.get("ready_to_finalize", False):
    if st.button("✅ Finalize and Save Details"):
        with st.spinner("Parsing our conversation and saving to Google Sheets..."):
            # The rest of your button logic remains exactly the same.
            full_conversation = "\n".join([f"{m['role'].title()}: {m['content']}" for m in st.session_state.messages])
            parsing_prompt = f"""
            Analyze the following conversation and extract: Party Size, Occasion, Vibe, Budget, Date, Special Requests, and Contact Email.
            Format the output as a single, clean JSON object. If a detail is missing, use "Not specified".
            Conversation:\n---\n{full_conversation}\n---
            """
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=parsing_prompt
                )
                json_string = response.text.strip().lstrip("```json").rstrip("```").strip()
                parsed_data = json.loads(json_string)

                new_row = [
                    parsed_data.get(key, "Not specified") for key in
                    ["Party Size", "Date", "Budget", "Vibe", "Special Requests", "Contact Email", "Occasion"]
                ]
                worksheet.append_row(new_row)
                st.success("Got it! I've saved the details and will be in touch with options shortly.")
                # Optional: Clear the conversation after a successful save
                # clear_conversation()
                # st.rerun()
            except Exception as e:
                st.error(f"An error occurred while saving: {e}")