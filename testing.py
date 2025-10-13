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


SYSTEM_PERSONA = (
    "Your name is yip hei "
)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PERSONA
)

chat_session = model.start_chat(
    history=[],
)

def send_message(event=None):
    user_message = user_input.get()
    if not user_message.strip():
        return

    chat_history.config(state=tk.NORMAL)

    chat_history.insert(tk.END, f"You: {user_message}\n\n")
    user_input.delete(0, tk.END)

    try:
        response = chat_session.send_message(user_message)
        chat_history.insert(tk.END, f"hei: {response.text}\n\n")

    except Exception as e:
        chat_history.insert(tk.END, f"Error: {e}\n\n")

    chat_history.config(state=tk.DISABLED)
    chat_history.see(tk.END)

main = tk.Tk()
main.title("Gemini Chat (Persona: hei)")
main.geometry("700x500")
main.config(bg="#E4E2E2")

main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

chat_frame = tk.Frame(main, bg="#EDECEC")
chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
chat_frame.grid_rowconfigure(0, weight=1)
chat_frame.grid_columnconfigure(0, weight=1)

chat_history = scrolledtext.ScrolledText(
    chat_frame,
    wrap=tk.WORD,
    state=tk.DISABLED,
    font=("Arial", 11),
    bg="#ffffff",
    padx=5,
    pady=5
)
chat_history.grid(row=0, column=0, sticky="nsew")

input_frame = tk.Frame(main, bg="#E4E2E2")
input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
input_frame.grid_columnconfigure(0, weight=1)

user_input = tk.Entry(input_frame, font=("Arial", 12))
user_input.grid(row=0, column=0, sticky="ew", ipady=8)
user_input.bind("<Return>", send_message)

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

main.mainloop()
