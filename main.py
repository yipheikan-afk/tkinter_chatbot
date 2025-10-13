import os
import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai
from dotenv import load_dotenv

# --- SETUP ---
# Load environment variables from a .env file
load_dotenv()

# Configure the Gemini API with your key
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("🔴 GEMINI_API_KEY not found in environment variables.")
    print("Please create a .env file and add your API key.")
    exit()

# --- MODEL INITIALIZATION ---
SYSTEM_PERSONA = (
    "Your name is hei "
)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
)
chat_session = model.start_chat(
    history=[],
    config=types.GenerateContentConfig(
    system_instruction=SYSTEM_PERSONA)
)



# --- FUNCTION ---
def send_message(event=None):
    """
    Gets user message, sends it to the AI, and displays the conversation.
    """
    user_message = user_input.get()
    # Don't send empty messages
    if not user_message.strip():
        return

    # Make the chat history widget writable to insert text
    chat_history.config(state=tk.NORMAL)

    # Display the user's message and clear the input box
    chat_history.insert(tk.END, f"You: {user_message}\n\n")
    user_input.delete(0, tk.END)

    try:
        # Send the message to the Gemini model and get the response
        response = chat_session.send_message(user_message)
        # Display the bot's response
        chat_history.insert(tk.END, f"Gemini: {response.text}\n\n")

    except Exception as e:
        # Display any errors that occur during the API call
        chat_history.insert(tk.END, f"Error: {e}\n\n")

    # Make the chat history read-only again
    chat_history.config(state=tk.DISABLED)
    # Automatically scroll to the end of the chat history
    chat_history.see(tk.END)


# --- GUI SETUP ---
# Create the main window
main = tk.Tk()
main.title("Gemini Chat")
main.geometry("700x500") # Increased height for better layout
main.config(bg="#E4E2E2")

# --- CONFIGURE GRID LAYOUT ---
# This makes the layout responsive.
# Row 0 (chat history) will expand vertically.
# Column 0 will expand horizontally.
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

# --- WIDGETS ---

# Frame for the chat history (top row)
# This frame will contain the scrolled text widget.
chat_frame = tk.Frame(main, bg="#EDECEC")
# sticky="nsew" makes the frame fill the entire cell of the grid.
chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
# Configure the grid inside this frame as well
chat_frame.grid_rowconfigure(0, weight=1)
chat_frame.grid_columnconfigure(0, weight=1)

# ScrolledText widget for chat history
chat_history = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    state=tk.DISABLED,  # Start as read-only
    font=("Arial", 11),
    bg="#ffffff",
    padx=5,
    pady=5
)
chat_history.grid(row=0, column=0, sticky="nsew")

# Frame for the user input and send button (bottom row)
input_frame = tk.Frame(main, bg="#E4E2E2")
input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
# Give the entry box column priority to expand
input_frame.grid_columnconfigure(0, weight=1)

# User input Entry box
user_input = tk.Entry(input_frame, font=("Arial", 12))
user_input.grid(row=0, column=0, sticky="ew", ipady=8)
# Bind the <Return> (Enter) key to the send_message function
user_input.bind("<Return>", send_message)

# Send button
send_button = tk.Button(
    input_frame,
    text="Send",
    font=("Arial", 11, "bold"),
    bg="#0078D4",
    fg="#ffffff",
    cursor="hand2",
    command=send_message
)
send_button.grid(row=0, column=1, padx=(10, 0), ipady=5, ipadx=10)


# --- START THE APP ---
main.mainloop()
