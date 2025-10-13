import os
import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("no api or not on environment")


# --- MODEL INITIALIZATION ---
SYSTEM_PERSONA = (
    "Your name is yip hei "
)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PERSONA
)

#
chat_session = model.start_chat(
    history=[],
)


# --- FUNCTION ---
def send_message(event=None):
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

        # Display the bot's response using the persona name
        chat_history.insert(tk.END, f"hei: {response.text}\n\n")  # Updated label

    except Exception as e:
        # Display any errors that occur during the API call
        # This will catch your 429 quota error if it happens again.
        chat_history.insert(tk.END, f"Error: {e}\n\n")

    # Make the chat history read-only again
    chat_history.config(state=tk.DISABLED)
    # Automatically scroll to the end of the chat history
    chat_history.see(tk.END)


# --- GUI SETUP ---
# Create the main window
main = tk.Tk()
main.title("Gemini Chat (Persona: hei)")  # Updated title for clarity
main.geometry("700x500")  # Increased height for better layout
main.config(bg="#E4E2E2")

# --- CONFIGURE GRID LAYOUT ---
# This makes the layout responsive.
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

# --- WIDGETS ---

# Frame for the chat history (top row)
chat_frame = tk.Frame(main, bg="#EDECEC")
chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
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
