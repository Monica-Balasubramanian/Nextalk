import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import requests

HOST = '127.0.0.1'
PORT = 1234
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Load or ask for logged-in username
if not os.path.exists("session.txt"):
    username = input("Enter your username: ")
    with open("session.txt", "w") as f:
        f.write(username)
else:
    with open("session.txt", "r") as f:
        username = f.read().strip()

# GUI Functions
def add_message(msg):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, msg + '\n')
    message_box.config(state=tk.DISABLED)

def listen():
    while True:
        try:
            msg = client.recv(2048).decode("utf-8")
            if msg:
                sender, content = msg.split("~", 1)
                add_message(f"[{sender}] {content}")
        except:
            break

def send():
    message = message_textbox.get()
    recipient = recipient_textbox.get()
    if recipient and message:
        # Send to socket server
        client.send(f"{recipient}~{message}".encode())
        # Send to database via Flask
        try:
            requests.post("http://127.0.0.1:5000/send", json={
                "sender": username,
                "recipient": recipient,
                "message": message
            })
        except:
            messagebox.showerror("Warning", "Could not save message to database.")
        message_textbox.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Recipient and message required")

# Tkinter UI Setup
root = tk.Tk()
root.title("Chat App")
root.geometry("600x500")

frame = tk.Frame(root)
frame.pack()

recipient_label = tk.Label(frame, text="To:")
recipient_label.grid(row=0, column=0)
recipient_textbox = tk.Entry(frame)
recipient_textbox.grid(row=0, column=1)

message_textbox = tk.Entry(frame, width=40)
message_textbox.grid(row=1, column=0, columnspan=2)

send_btn = tk.Button(frame, text="Send", command=send)
send_btn.grid(row=1, column=2)

message_box = scrolledtext.ScrolledText(root, width=70, height=25, state=tk.DISABLED)
message_box.pack(pady=10)

# Connect to server
client.connect((HOST, PORT))
client.send(username.encode())

# Start listening thread
threading.Thread(target=listen).start()

# Start GUI loop
root.mainloop()
